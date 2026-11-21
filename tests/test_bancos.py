"""Exercício 10.2: usuários no PostgreSQL.

Precisa de banco de verdade, informado por variável de ambiente (sem ela, os testes são pulados):
    LIVRARIA_TESTE_POSTGRES_URL=postgresql://postgres:teste@localhost:5432/livraria
No GitHub Actions o banco sobe como serviço do workflow. Cada teste começa com o banco vazio.

Além dos testes próprios do repositório, roda de novo todos os critérios de test_modulos.py com os usuários
no PostgreSQL, para provar que trocar a camada de dados não muda as regras.
"""
import os
import tempfile
import unittest

from livraria.aplicacao import montar_modulos
from livraria.compartilhado import RegraInvalida
from livraria.compartilhado.repositorio import RepositorioModulo
from livraria.modulos.usuarios import dados as dados_usuarios
from livraria.modulos.usuarios.dominio import Cliente, Favorito
from tests.test_modulos import ModulosTest

POSTGRES_URL = os.environ.get("LIVRARIA_TESTE_POSTGRES_URL")
PRECISA_DO_BANCO = unittest.skipUnless(POSTGRES_URL, "defina LIVRARIA_TESTE_POSTGRES_URL")


def limpar_bancos():
    import psycopg

    with psycopg.connect(POSTGRES_URL, autocommit=True) as conexao:
        conexao.execute("DROP TABLE IF EXISTS favoritos, clientes")


class BancosTest(unittest.TestCase):
    def setUp(self):
        limpar_bancos()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.pasta = tmp.name

    def montar(self, postgres_url):
        m = montar_modulos(self.pasta, postgres_url)
        if hasattr(m.usuarios.repo, "fechar"):
            self.addCleanup(m.usuarios.repo.fechar)
        return m


@PRECISA_DO_BANCO
class UsuariosPostgresTest(BancosTest):
    def repo(self):
        repo = dados_usuarios.criar_repositorio(None, POSTGRES_URL)
        self.addCleanup(repo.fechar)
        return repo

    def test_cria_tabelas_e_gera_id_pelo_serial(self):
        repo = self.repo()
        self.assertIsInstance(repo, RepositorioModulo)
        ana = repo.salvar(Cliente(0, "Ana", "ana@example.com", "Centro", ["Ficção", "Tecnologia"]))
        bia = repo.salvar(Cliente(0, "Bia", "bia@example.com", "Jardim", []))
        self.assertEqual((ana.id, bia.id), (1, 2))
        self.assertEqual(self.repo().listar(Cliente)[0].interesses, ["Ficção", "Tecnologia"])

    def test_favorito_tem_chave_composta_e_cascata(self):
        repo = self.repo()
        ana = repo.salvar(Cliente(0, "Ana", "ana@example.com", "Centro", []))
        repo.salvar(Favorito(ana.id, 3))
        repo.salvar(Favorito(ana.id, 3))  # ON CONFLICT: não duplica
        self.assertEqual(repo.listar(Favorito), [Favorito(ana.id, 3)])
        repo.remover(Favorito(ana.id, 3))
        self.assertEqual(repo.listar(Favorito), [])

    def test_erro_no_meio_da_transacao_desfaz_tudo(self):
        repo = self.repo()
        with self.assertRaises(RuntimeError):
            with repo.transacao():
                repo.salvar(Cliente(0, "Ana", "ana@example.com", "Centro", []))
                raise RuntimeError("falha simulada")
        self.assertEqual(repo.listar(Cliente), [])

    def test_banco_recusa_email_repetido(self):
        import psycopg

        repo = self.repo()
        repo.salvar(Cliente(0, "Ana", "ana@example.com", "Centro", []))
        with self.assertRaises(psycopg.errors.UniqueViolation):
            repo.salvar(Cliente(0, "Outra", "ana@example.com", "Centro", []))

    def test_cadastro_pela_api_do_modulo_persiste_no_postgres(self):
        m = self.montar(POSTGRES_URL)
        for i, nome in enumerate(("Ana", "Bruno", "Carla", "Diego"), 1):
            self.assertEqual(m.usuarios.cadastrar(nome, f"{nome.lower()}@example.com", "Centro", "Literatura"), i)
        with self.assertRaises(RegraInvalida):
            m.usuarios.cadastrar("Ana", "ANA@example.com", "Centro")
        reaberto = self.montar(POSTGRES_URL)
        self.assertEqual(reaberto.usuarios.entrar("carla@example.com").nome, "Carla")


@PRECISA_DO_BANCO
class CriteriosComBancosTest(ModulosTest):
    """Mesmos critérios C01–C07, C09 e C10 de test_modulos.py, agora com usuários no PostgreSQL."""

    def setUp(self):
        limpar_bancos()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.m = montar_modulos(tmp.name, POSTGRES_URL)
        self.addCleanup(self.m.usuarios.repo.fechar)


if __name__ == "__main__":
    unittest.main()
