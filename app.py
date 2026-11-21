"""Ponto de entrada do servidor: monta a camada de negócios (módulos com dados em LIVRARIA_DADOS) e a API Flask.

Local:   python app.py
Azure:   gunicorn --bind=0.0.0.0:8000 --workers 1 --threads 8 app:app
"""
import os

from livraria.aplicacao import montar_modulos
from livraria.servidor.app import create_app


def criar_app(pasta_dados=None, mongo_url=None, postgres_url=None):
    """Sem pasta informada (produção), lê LIVRARIA_DADOS, LIVRARIA_MONGO_URL e LIVRARIA_POSTGRES_URL."""
    if pasta_dados is None:
        pasta_dados = os.environ.get("LIVRARIA_DADOS", "dados")
        mongo_url = os.environ.get("LIVRARIA_MONGO_URL")
        postgres_url = os.environ.get("LIVRARIA_POSTGRES_URL")
    return create_app(montar_modulos(pasta_dados, mongo_url, postgres_url))


def __getattr__(nome):
    """`app:app` (padrão do Azure App Service) cria o app só quando o gunicorn pede, não ao importar nos testes."""
    if nome == "app":
        globals()["app"] = criar_app()
        return globals()["app"]
    raise AttributeError(nome)


if __name__ == "__main__":
    criar_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=False)
