"""Armazenamento de usuários em arquivo TXT. Começa vazio."""
from livraria.compartilhado.repositorio_txt import RepositorioTxt
from livraria.modulos.usuarios.dominio import Cliente, Favorito

CHAVES = {Favorito: ("cliente_id", "livro_id")}


def criar_repositorio(caminho):
    return RepositorioTxt(caminho, (Cliente, Favorito), chaves=CHAVES)
