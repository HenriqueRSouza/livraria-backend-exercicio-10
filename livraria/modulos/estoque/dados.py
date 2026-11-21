"""Armazenamento do estoque (estoque.txt) e dados de exemplo gravados na primeira execução."""
from livraria.compartilhado.repositorio_txt import RepositorioTxt
from livraria.modulos.estoque.dominio import Alerta, Estoque, Loja


def dados_exemplo():
    return [
        Loja(1, "Unidade Centro", "Centro", "Rua das Flores, 10", "Seg–Sáb 9h–18h", "Pix, cartão (simulados)",
             "Retirada, acessibilidade", True, "Clube do livro aos sábados"),
        Loja(2, "Unidade Jardim", "Jardim", "Av. Verde, 22", "Seg–Sáb 10h–19h", "Pix, cartão (simulados)",
             "Retirada", False, "Oficina de leitura mensal"),
        Estoque(1, 1, 1, "Literatura"), Estoque(1, 2, 2, "Ficção"), Estoque(2, 1, 0, "Literatura"),
        Estoque(2, 2, 1, "Ficção"), Estoque(3, 1, 2, "Tecnologia"), Estoque(3, 2, 0, "Tecnologia"),
    ] + [Estoque(edicao, loja, quantidade, secao)  # edições 4–13 do catálogo (livros 3–12)
         for edicao, secao in ((4, "Literatura"), (5, "Literatura"), (6, "Literatura"), (7, "Literatura"),
                               (8, "Literatura"), (9, "Tecnologia"), (10, "Tecnologia"), (11, "Infantil"),
                               (12, "Ficção"), (13, "História"))
         for loja, quantidade in ((1, 3), (2, 1))]


def criar_repositorio(caminho):
    chaves = {Estoque: ("edicao_id", "loja_id"), Alerta: ("cliente_id", "edicao_id", "loja_id")}
    return RepositorioTxt(caminho, (Loja, Estoque, Alerta), chaves, dados_exemplo())
