"""RepositorioPostgres: implementa RepositorioModulo guardando os registros de UM módulo em tabelas PostgreSQL.

Usado pelo módulo de usuários com o Azure Database for PostgreSQL (Exercício 10.2). Cada entidade tem a sua
tabela (Cliente -> clientes, Favorito -> favoritos), criada pelo DDL que o módulo informa. As colunas têm os
mesmos nomes dos campos do dataclass.

- Registro com id 0 recebe o id do SERIAL do banco (INSERT ... RETURNING id).
- Os demais são gravados com INSERT ... ON CONFLICT (chave) DO UPDATE (upsert).
- transacao() abre uma transação de verdade no banco: tudo o que for salvo dentro dela é confirmado junto
  (COMMIT) ou desfeito (ROLLBACK) se der erro.
"""
import threading
from contextlib import contextmanager
from dataclasses import astuple, fields

from psycopg import sql
from psycopg_pool import ConnectionPool

from livraria.compartilhado.repositorio import RepositorioModulo


class RepositorioPostgres(RepositorioModulo):
    def __init__(self, url, tabelas, chaves=None, ddl="", dados_iniciais=()):
        """tabelas: {Tipo: "nome_da_tabela"}; chaves: campos que identificam registros sem "id"; ddl: CREATE TABLE."""
        self.tabelas = tabelas
        self.chaves = chaves or {}
        self.local = threading.local()
        self.pool = ConnectionPool(url, min_size=1, max_size=4, open=True, timeout=20,
                                   kwargs={"connect_timeout": 10})
        with self.transacao():
            with self._cursor() as cur:
                if ddl:
                    cur.execute(ddl)
                vazio = all(not self.listar(tipo) for tipo in tabelas)
            if vazio:
                for registro in dados_iniciais:
                    self.salvar(registro)

    def listar(self, tipo):
        colunas = [f.name for f in fields(tipo)]
        consulta = sql.SQL("SELECT {} FROM {} ORDER BY {}").format(
            sql.SQL(", ").join(map(sql.Identifier, colunas)), sql.Identifier(self.tabelas[tipo]),
            sql.SQL(", ").join(map(sql.Identifier, self._campos(tipo))))
        with self._cursor() as cur:
            cur.execute(consulta)
            return [tipo(*linha) for linha in cur.fetchall()]

    def salvar(self, registro):
        tipo = type(registro)
        tabela = sql.Identifier(self.tabelas[tipo])
        colunas = [f.name for f in fields(tipo)]
        valores = dict(zip(colunas, astuple(registro)))
        chaves = self._campos(tipo)
        with self._cursor() as cur:
            if chaves == ("id",) and registro.id == 0:
                sem_id = [c for c in colunas if c != "id"]
                cur.execute(sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING id").format(
                    tabela, sql.SQL(", ").join(map(sql.Identifier, sem_id)),
                    sql.SQL(", ").join(sql.Placeholder(c) for c in sem_id)), valores)
                registro.id = cur.fetchone()[0]
                return registro
            outras = [c for c in colunas if c not in chaves]
            conflito = (sql.SQL("DO UPDATE SET {}").format(sql.SQL(", ").join(
                sql.SQL("{0} = EXCLUDED.{0}").format(sql.Identifier(c)) for c in outras))
                if outras else sql.SQL("DO NOTHING"))
            cur.execute(sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT ({}) {}").format(
                tabela, sql.SQL(", ").join(map(sql.Identifier, colunas)),
                sql.SQL(", ").join(sql.Placeholder(c) for c in colunas),
                sql.SQL(", ").join(map(sql.Identifier, chaves)), conflito), valores)
            return registro

    def remover(self, registro):
        chaves = self._campos(type(registro))
        with self._cursor() as cur:
            cur.execute(sql.SQL("DELETE FROM {} WHERE {}").format(
                sql.Identifier(self.tabelas[type(registro)]),
                sql.SQL(" AND ").join(sql.SQL("{} = {}").format(sql.Identifier(c), sql.Placeholder(c))
                                      for c in chaves)),
                {c: getattr(registro, c) for c in chaves})

    @contextmanager
    def transacao(self):
        if getattr(self.local, "conexao", None) is not None:  # já dentro de uma transação
            yield
            return
        with self.pool.connection() as conexao:  # COMMIT ao sair; ROLLBACK se houver exceção
            self.local.conexao = conexao
            try:
                yield
            finally:
                self.local.conexao = None

    def fechar(self):
        self.pool.close()

    @contextmanager
    def _cursor(self):
        with self.transacao():
            with self.local.conexao.cursor() as cur:
                yield cur

    def _campos(self, tipo):
        return self.chaves.get(tipo, ("id",))
