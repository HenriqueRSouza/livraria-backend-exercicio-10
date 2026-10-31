"""Regras das camadas do back-end verificadas no código-fonte (o cliente MVC está no repositório do front-end).

1. Routes só usam a API pública dos módulos (camada de Negócios), nunca dominio.py ou dados.py.
2. Negócios não conhecem HTTP: módulos não importam Flask nem o servidor.
3. Um módulo só usa outro pela api.py dele, e cada módulo grava no seu próprio arquivo de dados.
"""
import ast
import tempfile
import unittest
from pathlib import Path

from livraria.aplicacao import montar_modulos

LIVRARIA = Path(__file__).resolve().parent.parent / "livraria"
MODULOS = sorted(p.name for p in (LIVRARIA / "modulos").iterdir() if p.is_dir() and not p.name.startswith("_"))


def importacoes(arquivo):
    for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
        if isinstance(no, ast.ImportFrom) and no.module:
            yield no.module
        elif isinstance(no, ast.Import):
            yield from (a.name for a in no.names)


class ServidorCamadasTest(unittest.TestCase):
    def test_modulos_da_camada_de_negocios(self):
        self.assertEqual(MODULOS, ["busca", "catalogo", "estoque", "notificacoes", "pagamentos", "pedidos", "usuarios"])

    def test_rotas_so_usam_a_api_dos_modulos(self):
        for arquivo in (LIVRARIA / "servidor").glob("*.py"):
            for nome in importacoes(arquivo):
                self.assertFalse(nome.startswith("livraria.modulos"), f"{arquivo.name} importa {nome}")

    def test_negocios_nao_conhecem_http(self):
        for arquivo in (LIVRARIA / "modulos").rglob("*.py"):
            for nome in importacoes(arquivo):
                self.assertFalse(nome.startswith(("flask", "livraria.servidor", "livraria.aplicacao")),
                                 f"{arquivo.relative_to(LIVRARIA)} importa {nome}")

    def test_modulo_so_usa_outro_pela_api(self):
        for modulo in MODULOS:
            for arquivo in (LIVRARIA / "modulos" / modulo).glob("*.py"):
                for nome in importacoes(arquivo):
                    partes = nome.split(".")
                    if partes[:2] == ["livraria", "modulos"] and len(partes) > 2 and partes[2] != modulo:
                        self.assertEqual(partes[3:], ["api"], f"{arquivo.relative_to(LIVRARIA)} importa {nome}")

    def test_cada_modulo_tem_seu_arquivo_de_dados(self):
        with tempfile.TemporaryDirectory() as pasta:
            montar_modulos(pasta)
            arquivos = sorted(p.name for p in Path(pasta).glob("*.txt"))
        self.assertEqual(arquivos, ["catalogo.txt", "estoque.txt", "notificacoes.txt", "pagamentos.txt",
                                    "pedidos.txt", "usuarios.txt"])  # busca só lê o catálogo


if __name__ == "__main__":
    unittest.main()
