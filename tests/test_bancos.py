"""Exercícios 10.1 e 10.2: catálogo no MongoDB (Cosmos DB for MongoDB) e usuários no PostgreSQL.

Precisam de bancos de verdade, informados por variáveis de ambiente (sem elas, os testes são pulados):
    LIVRARIA_TESTE_MONGO_URL=mongodb://localhost:27017/livraria_teste
    LIVRARIA_TESTE_POSTGRES_URL=postgresql://postgres:teste@localhost:5432/livraria
No GitHub Actions os dois bancos sobem como serviços do workflow. Cada teste começa com os bancos vazios.

Além dos testes próprios dos repositórios, roda de novo todos os critérios de test_modulos.py com o catálogo
no MongoDB e os usuários no PostgreSQL, para provar que trocar a camada de dados não muda as regras.
"""
import os
import tempfile
import unittest

from livraria.aplicacao import montar_modulos
from livraria.compartilhado import RegraInvalida
from livraria.compartilhado.repositorio import RepositorioModulo
from livraria.modulos.catalogo import dados as dados_catalogo
from livraria.modulos.catalogo.dominio import Avaliacao, Livro
from livraria.modulos.usuarios import dados as dados_usuarios
from livraria.modulos.usuarios.dominio import Cliente, Favorito
from tests.test_modulos import ModulosTest

MONGO_URL = os.environ.get("LIVRARIA_TESTE_MONGO_URL")
POSTGRES_URL = os.environ.get("LIVRARIA_TESTE_POSTGRES_URL")
PRECISA_DOS_BANCOS = unittest.skipUnless(MONGO_URL and POSTGRES_URL,
                                         "defina LIVRARIA_TESTE_MONGO_URL e LIVRARIA_TESTE_POSTGRES_URL")


def limpar_bancos():
    from pymongo import MongoClient
    import psycopg

    with MongoClient(MONGO_URL) as cliente:
        cliente.drop_database(cliente.get_default_database())
    with psycopg.connect(POSTGRES_URL, autocommit=True) as conexao:
        conexao.execute("DROP TABLE IF EXISTS favoritos, clientes")


class BancosTest(unittest.TestCase):
    def setUp(self):
        limpar_bancos()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.pasta = tmp.name

    def montar(self, mongo_url, postgres_url):
        m = montar_modulos(self.pasta, mongo_url, postgres_url)
        for repo in (m.catalogo.repo, m.usuarios.repo):
            if hasattr(repo, "fechar"):
                self.addCleanup(repo.fechar)
        return m


@PRECISA_DOS_BANCOS
class CatalogoMongoTest(BancosTest):
    def repo(self):
        repo = dados_catalogo.criar_repositorio(None, MONGO_URL)
        self.addCleanup(repo.fechar)
        return repo

    def test_grava_pelo_menos_10_livros_uma_vez_so(self):
        repo = self.repo()
        self.assertIsInstance(repo, RepositorioModulo)
        self.assertGreaterEqual(len(repo.listar(Livro)), 10)
        self.repo()  # reabrir não duplica os dados de exemplo
        livros = self.repo().listar(Livro)
        self.assertEqual([l.id for l in livros], list(range(1, 13)))
        documento = repo.banco["livro"].find_one({"_id": 3})
        self.assertEqual((documento["titulo"], documento["autor"]), ("Dom Casmurro", "Machado de Assis"))

    def test_id_novo_continua_depois_dos_dados_de_exemplo_e_atualiza_sem_duplicar(self):
        repo = self.repo()
        livro = repo.salvar(Livro(0, "Grande Sertão: Veredas", "Guimarães Rosa", "Literatura", "Riobaldo."))
        self.assertEqual(livro.id, 13)
        livro.genero = "Clássico"
        repo.salvar(livro)
        self.assertEqual([l.genero for l in self.repo().listar(Livro) if l.id == 13], ["Clássico"])
        repo.remover(livro)
        self.assertEqual(len(repo.listar(Livro)), 12)

    def test_avaliacao_gravada_no_mongo(self):
        m = self.montar(MONGO_URL, POSTGRES_URL)
        ana = m.usuarios.cadastrar("Ana", "ana@example.com", "Centro")
        m.catalogo.avaliar(ana, "Ana", 3, 5, "Clássico")
        self.assertEqual(self.repo().listar(Avaliacao)[-1].texto, "Clássico")


@PRECISA_DOS_BANCOS
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
        m = self.montar(None, POSTGRES_URL)
        for i, nome in enumerate(("Ana", "Bruno", "Carla", "Diego"), 1):
            self.assertEqual(m.usuarios.cadastrar(nome, f"{nome.lower()}@example.com", "Centro", "Literatura"), i)
        with self.assertRaises(RegraInvalida):
            m.usuarios.cadastrar("Ana", "ANA@example.com", "Centro")
        reaberto = self.montar(None, POSTGRES_URL)
        self.assertEqual(reaberto.usuarios.entrar("carla@example.com").nome, "Carla")


@PRECISA_DOS_BANCOS
class CriteriosComBancosTest(ModulosTest):
    """Mesmos critérios C01–C07, C09 e C10 de test_modulos.py, agora com MongoDB e PostgreSQL."""

    def setUp(self):
        limpar_bancos()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.m = montar_modulos(tmp.name, MONGO_URL, POSTGRES_URL)
        self.addCleanup(self.m.catalogo.repo.fechar)
        self.addCleanup(self.m.usuarios.repo.fechar)


if __name__ == "__main__":
    unittest.main()
