"""Aplicação (app/servidor): cria o Flask, registra as rotas da API e libera o front-end no CORS.

O back-end não entrega telas nem arquivos do cliente: o front-end é outro projeto, publicado em outro
endereço, e conversa com esta API só por HTTP/REST em JSON.
"""
import os

from flask import Flask, request

from livraria.servidor.rotas import criar_rotas


def origens_permitidas():
    """LIVRARIA_CORS_ORIGENS: endereços do front-end separados por vírgula ("*" libera qualquer um)."""
    return {o.strip().rstrip("/") for o in os.environ.get("LIVRARIA_CORS_ORIGENS", "*").split(",") if o.strip()}


def create_app(modulos):
    app = Flask(__name__, static_folder=None)
    app.secret_key = os.environ.get("LIVRARIA_SECRET", "chave-local-apenas-demonstracao")
    app.json.ensure_ascii = False
    app.register_blueprint(criar_rotas(modulos))
    origens = origens_permitidas()

    @app.after_request
    def cors(resposta):
        origem = request.headers.get("Origin")
        if origem and ("*" in origens or origem.rstrip("/") in origens):
            resposta.headers["Access-Control-Allow-Origin"] = origem
            resposta.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            resposta.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            resposta.headers["Access-Control-Max-Age"] = "600"
            resposta.headers["Vary"] = "Origin"
        return resposta

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/")
    def inicio():
        return {"api": "Livraria (back-end)", "health": "/health", "livros": "/api/livros"}

    return app
