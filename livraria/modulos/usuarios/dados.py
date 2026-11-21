"""Armazenamento de usuários. Começa vazio.

Produção (Exercício 10.2): banco SQL Azure Database for PostgreSQL, quando há uma string de conexão.
Sem ela (testes e desenvolvimento): arquivo usuarios.txt.
"""
from livraria.compartilhado.repositorio_postgres import RepositorioPostgres
from livraria.compartilhado.repositorio_txt import RepositorioTxt
from livraria.modulos.usuarios.dominio import Cliente, Favorito

CHAVES = {Favorito: ("cliente_id", "livro_id")}

# O livro do favorito fica no catálogo (outro banco), por isso livro_id não tem chave estrangeira.
DDL = """
CREATE TABLE IF NOT EXISTS clientes (
    id          SERIAL PRIMARY KEY,
    nome        TEXT NOT NULL CHECK (nome <> ''),
    email       TEXT NOT NULL UNIQUE CHECK (email = lower(email)),
    bairro      TEXT NOT NULL CHECK (bairro <> ''),
    interesses  TEXT[] NOT NULL DEFAULT '{}',
    criado_em   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS favoritos (
    cliente_id  INTEGER NOT NULL REFERENCES clientes (id) ON DELETE CASCADE,
    livro_id    INTEGER NOT NULL,
    PRIMARY KEY (cliente_id, livro_id)
);
"""


def criar_repositorio(caminho, postgres_url=None):
    if postgres_url:
        return RepositorioPostgres(postgres_url, {Cliente: "clientes", Favorito: "favoritos"}, CHAVES, DDL)
    return RepositorioTxt(caminho, (Cliente, Favorito), chaves=CHAVES)
