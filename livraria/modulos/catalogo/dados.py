"""Armazenamento do catálogo e dados de exemplo gravados na primeira execução.

Produção (Exercício 10.1): banco NoSQL Azure Cosmos DB for MongoDB, quando há uma string de conexão.
Sem ela (testes e desenvolvimento): arquivo catalogo.txt.
"""
from livraria.compartilhado.repositorio_mongo import RepositorioMongo
from livraria.compartilhado.repositorio_txt import RepositorioTxt
from livraria.modulos.catalogo.dominio import Avaliacao, Edicao, Livro, Promocao

TIPOS = (Livro, Edicao, Promocao, Avaliacao)

LIVROS = [
    Livro(1, "A Casa das Marés", "L. Andrade", "Ficção", "Uma viagem às memórias de uma cidade costeira."),
    Livro(2, "Python para Todos", "Ana Ribeiro", "Tecnologia", "Introdução prática à programação."),
    Livro(3, "Dom Casmurro", "Machado de Assis", "Literatura",
          "Bentinho revisita a juventude e o ciúme que sente de Capitu."),
    Livro(4, "Memórias Póstumas de Brás Cubas", "Machado de Assis", "Literatura",
          "Um defunto-autor narra a própria vida com ironia."),
    Livro(5, "O Cortiço", "Aluísio Azevedo", "Literatura", "A vida coletiva em um cortiço do Rio de Janeiro."),
    Livro(6, "Vidas Secas", "Graciliano Ramos", "Literatura", "Uma família de retirantes atravessa o sertão."),
    Livro(7, "A Hora da Estrela", "Clarice Lispector", "Literatura", "Macabéa, nordestina no Rio, e o narrador que a cria."),
    Livro(8, "Engenharia de Software Moderna", "Marco Tulio Valente", "Tecnologia",
          "Princípios e práticas de desenvolvimento de software."),
    Livro(9, "Código Limpo", "Robert C. Martin", "Tecnologia", "Boas práticas para escrever código legível."),
    Livro(10, "O Pequeno Príncipe", "Antoine de Saint-Exupéry", "Infantil",
          "Um piloto perdido no deserto conhece um pequeno príncipe."),
    Livro(11, "1984", "George Orwell", "Ficção", "Um Estado que vigia tudo e reescreve o passado."),
    Livro(12, "Sapiens", "Yuval Noah Harari", "História", "Uma breve história da humanidade."),
]

# Edições 1–3 vêm do exercício anterior; os livros 3–12 têm uma edição cada (id = livro + 1).
EDICOES = [Edicao(1, 1, "Brochura", 2024, 5000), Edicao(2, 1, "Capa dura", 2025, 7500),
           Edicao(3, 2, "Brochura", 2024, 8000)] + [
    Edicao(livro + 1, livro, nome, ano, preco) for livro, nome, ano, preco in (
        (3, "Brochura", 2019, 2990), (4, "Brochura", 2019, 3290), (5, "Bolso", 2018, 2490),
        (6, "Brochura", 2020, 4490), (7, "Brochura", 2020, 3990), (8, "Brochura", 2020, 9900),
        (9, "Brochura", 2009, 8990), (10, "Capa dura", 2015, 3490), (11, "Brochura", 2009, 4590),
        (12, "Brochura", 2015, 6990))]


def dados_exemplo():
    return LIVROS + EDICOES + [
        Promocao(1, 1, "Oferta de demonstração", 1000, True),
        Promocao(2, 4, "Semana dos clássicos", 500, True),
        Avaliacao(1, 1, 5, "Envolvente", "Leitora demo"),
    ]


def criar_repositorio(caminho, mongo_url=None):
    """mongo_url: o banco é o do caminho da URL (ex.: mongodb://.../livraria) ou "livraria"."""
    if mongo_url:
        return RepositorioMongo(mongo_url, TIPOS, dados_iniciais=dados_exemplo())
    return RepositorioTxt(caminho, TIPOS, dados_iniciais=dados_exemplo())
