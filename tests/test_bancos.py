"""Exercício 10.1: catálogo no MongoDB (Cosmos DB for MongoDB).

Precisa de banco de verdade, informado por variável de ambiente (sem ela, os testes são pulados):
    LIVRARIA_TESTE_MONGO_URL=mongodb://localhost:27017/livraria_teste
No GitHub Actions o banco sobe como serviço do workflow. Cada teste começa com o banco vazio.

Além dos testes próprios do repositório, roda de novo todos os critérios de test_modulos.py com o catálogo
no MongoDB, para provar que trocar a camada de dados não muda as regras.
"""
import os
import tempfile
import unittest

from livraria.aplicacao import montar_modulos
from livraria.compartilhado.repositorio import RepositorioModulo
from livraria.modulos.catalogo import dados as dados_catalogo
from livraria.modulos.catalogo.dominio import Avaliacao, Livro
from tests.test_modulos import ModulosTest

MONGO_URL = os.environ.get("LIVRARIA_TESTE_MONGO_URL")
PRECISA_DO_BANCO = unittest.skipUnless(MONGO_URL, "defina LIVRARIA_TESTE_MONGO_URL")


def limpar_bancos():
    from pymongo import MongoClient

    with MongoClient(MONGO_URL) as cliente:
        cliente.drop_database(cliente.get_default_database())


class BancosTest(unittest.TestCase):
    def setUp(self):
        limpar_bancos()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.pasta = tmp.name

    def montar(self, mongo_url):
        m = montar_modulos(self.pasta, mongo_url)
        if hasattr(m.catalogo.repo, "fechar"):
            self.addCleanup(m.catalogo.repo.fechar)
        return m


@PRECISA_DO_BANCO
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
        m = self.montar(MONGO_URL)
        ana = m.usuarios.cadastrar("Ana", "ana@example.com", "Centro")
        m.catalogo.avaliar(ana, "Ana", 3, 5, "Clássico")
        self.assertEqual(self.repo().listar(Avaliacao)[-1].texto, "Clássico")


@PRECISA_DO_BANCO
class CriteriosComBancosTest(ModulosTest):
    """Mesmos critérios C01–C07, C09 e C10 de test_modulos.py, agora com o catálogo no MongoDB."""

    def setUp(self):
        limpar_bancos()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.m = montar_modulos(tmp.name, MONGO_URL)
        self.addCleanup(self.m.catalogo.repo.fechar)


if __name__ == "__main__":
    unittest.main()
