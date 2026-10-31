"""C08–C10 pela API REST (JSON), login por token, CORS para o front-end e /health."""
import os
import tempfile
import unittest
from unittest import mock

from app import criar_app


class ApiRestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.app = criar_app(self.tmp.name)
        self.app.testing = True
        self.web = self.app.test_client()
        self.auth = {}

    def entrar(self):
        resposta = self.web.post("/api/clientes", json={"nome": "Ana", "email": "ana@example.com", "bairro": "Centro",
                                                       "interesses": "Ficção"})
        self.assertEqual(resposta.status_code, 201)
        self.auth = {"Authorization": f"Bearer {resposta.json['token']}"}
        return resposta.json["cliente"]

    def get(self, url):
        return self.web.get(url, headers=self.auth)

    def post(self, url, dados=None):
        return self.web.post(url, json=dados or {}, headers=self.auth)

    def put(self, url, dados=None):
        return self.web.put(url, json=dados or {}, headers=self.auth)

    def test_health_e_inicio(self):
        self.assertEqual(self.web.get("/health").json, {"status": "ok"})
        self.assertEqual(self.web.get("/").json["livros"], "/api/livros")

    def test_c01_c03_consultas_publicas(self):
        self.assertEqual([l["titulo"] for l in self.web.get("/api/livros?titulo=mares").json], ["A Casa das Marés"])
        self.assertEqual(self.web.get("/api/livros?genero=inexistente").json, [])
        livro = self.web.get("/api/livros/1").json
        self.assertEqual((livro["media"], livro["total_avaliacoes"], len(livro["edicoes"])), (5.0, 1, 2))
        self.assertEqual(livro["edicoes"][0]["preco_final_centavos"], 4000)
        self.assertEqual(livro["edicoes"][0]["estoques"][0]["secao"], "Literatura")
        resposta = self.web.get("/api/livros/999")
        self.assertEqual((resposta.status_code, resposta.json["erro"]), (404, "Livro não encontrado."))
        self.assertEqual([l["nome"] for l in self.web.get("/api/lojas?bairro=centro").json], ["Unidade Centro"])

    def test_login_por_token(self):
        self.assertEqual(self.web.get("/api/sessao").json, {"cliente": None})
        self.assertEqual(self.web.get("/api/minha-area").status_code, 401)
        ana = self.entrar()
        self.assertEqual(self.get("/api/sessao").json["cliente"]["id"], ana["id"])
        repetido = self.web.post("/api/clientes", json={"nome": "Ana", "email": "ANA@example.com", "bairro": "Centro"})
        self.assertEqual((repetido.status_code, repetido.json["erro"]), (400, "Email já cadastrado."))
        entrada = self.web.post("/api/sessao", json={"email": "ana@example.com"}).json
        self.assertEqual(entrada["cliente"]["nome"], "Ana")
        self.assertTrue(entrada["token"])
        self.assertEqual(self.web.post("/api/sessao", json={"email": "x@example.com"}).status_code, 400)
        self.assertEqual(self.web.delete("/api/sessao").status_code, 204)
        falso = {"Authorization": "Bearer token-falsificado"}
        self.assertEqual(self.web.get("/api/minha-area", headers=falso).status_code, 401)
        self.assertEqual(self.web.post("/api/reservas", json={"edicao_id": 1, "loja_id": 1}).status_code, 401)

    def test_token_de_outro_servidor_nao_vale(self):
        self.entrar()
        with mock.patch.dict(os.environ, {"LIVRARIA_SECRET": "outra-chave"}):
            outro = criar_app(self.tmp.name).test_client()
        self.assertEqual(outro.get("/api/minha-area", headers=self.auth).status_code, 401)

    def test_c08_reserva_retirada_e_historico(self):
        self.entrar()
        resposta = self.post("/api/reservas", {"edicao_id": "1", "loja_id": "1"})
        self.assertEqual(resposta.status_code, 201)
        self.assertIn("RES-000001 por R$ 40,00", resposta.json["mensagem"])
        self.assertEqual(self.web.get("/api/livros/1").json["edicoes"][0]["estoques"][0]["quantidade"], 0)
        self.assertIn("concluída", self.post("/api/reservas/RES-000001/retirada").json["mensagem"])
        area = self.get("/api/minha-area").json
        self.assertEqual(area["historico"]["pontos"], 40)
        self.assertEqual(area["historico"]["reservas"][0]["estado"], "retirada")
        self.assertEqual(self.post("/api/reservas/RES-000001/cancelamento").status_code, 400)

    def test_c08_favoritos_alerta_reposicao_e_compra(self):
        self.entrar()
        self.put("/api/favoritos/1")
        self.assertEqual([b["id"] for b in self.get("/api/minha-area").json["favoritos"]], [1])
        self.web.delete("/api/favoritos/1", headers=self.auth)
        self.assertEqual(self.post("/api/alertas", {"edicao_id": 2, "loja_id": 1}).status_code, 201)
        self.post("/api/estoque/reposicao", {"edicao_id": 2, "loja_id": 1})
        self.assertIn("reposicao", [n["tipo"] for n in self.get("/api/minha-area").json["notificacoes"]])
        self.assertEqual(self.post("/api/compras", {"edicao_id": 2, "loja_id": 1}).status_code, 201)
        self.assertEqual(self.get("/api/minha-area").json["historico"]["pontos"], 75)
        resposta = self.post("/api/compras", {"edicao_id": 2, "loja_id": 1})
        self.assertEqual((resposta.status_code, resposta.json["erro"]), (400, "Sem estoque nesta unidade/edição."))
        self.assertEqual(self.post("/api/compras", {"edicao_id": "abc"}).json["erro"], "Dados do formulário inválidos.")

    def test_c09_avaliacao(self):
        self.assertEqual(self.put("/api/livros/1/avaliacao", {"nota": 4}).status_code, 401)
        self.entrar()
        resposta = self.put("/api/livros/1/avaliacao", {"nota": "4", "texto": "Gostei"})
        self.assertEqual(resposta.json["mensagem"], "Avaliação registrada. Obrigado!")
        self.assertEqual(self.web.get("/api/livros/1").json["media"], 4.5)
        self.assertIn("nota deve ser", self.put("/api/livros/1/avaliacao", {"nota": 9}).json["erro"])
        self.assertEqual(self.put("/api/livros/99/avaliacao", {"nota": 5}).status_code, 400)

    def test_c10_cupom(self):
        self.entrar()
        resposta = self.post("/api/reservas", {"edicao_id": 1, "loja_id": 2, "cupom": "leitura10"})
        self.assertIn("R$ 36,00 com cupom LEITURA10", resposta.json["mensagem"])
        self.assertIn("já utilizado", self.post("/api/compras", {"edicao_id": 1, "loja_id": 2, "cupom": "LEITURA10"}).json["erro"])
        resposta = self.post("/api/compras", {"edicao_id": 1, "loja_id": 2, "cupom": ""})
        self.assertIn("R$ 40,00 (sem cobrança real)", resposta.json["mensagem"])

    def test_dados_compartilhados_entre_instancias(self):
        """Simula dois workers do gunicorn lendo a mesma pasta de dados (e aceitando o mesmo token)."""
        self.entrar()
        self.post("/api/reservas", {"edicao_id": 1, "loja_id": 1})
        outro = criar_app(self.tmp.name).test_client()
        self.assertEqual(outro.get("/api/livros/1").json["edicoes"][0]["estoques"][0]["quantidade"], 0)
        self.assertEqual(outro.get("/api/minha-area", headers=self.auth).status_code, 200)


class CorsTest(unittest.TestCase):
    FRONT = "https://front.exemplo.net"

    def cliente(self, origens):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        with mock.patch.dict(os.environ, {"LIVRARIA_CORS_ORIGENS": origens}):
            return criar_app(tmp.name).test_client()

    def test_front_end_liberado_inclusive_no_preflight(self):
        web = self.cliente(self.FRONT + "/")
        resposta = web.get("/api/livros", headers={"Origin": self.FRONT})
        self.assertEqual(resposta.headers["Access-Control-Allow-Origin"], self.FRONT)
        preflight = web.options("/api/reservas", headers={
            "Origin": self.FRONT, "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization, content-type"})
        self.assertEqual(preflight.status_code, 200)
        self.assertIn("Authorization", preflight.headers["Access-Control-Allow-Headers"])
        self.assertIn("POST", preflight.headers["Access-Control-Allow-Methods"])
        erro = web.post("/api/reservas", json={}, headers={"Origin": self.FRONT})  # 401 também precisa de CORS
        self.assertEqual((erro.status_code, erro.headers["Access-Control-Allow-Origin"]), (401, self.FRONT))

    def test_outra_origem_bloqueada(self):
        resposta = self.cliente(self.FRONT).get("/api/livros", headers={"Origin": "https://site-estranho.com"})
        self.assertNotIn("Access-Control-Allow-Origin", resposta.headers)

    def test_padrao_libera_qualquer_origem(self):
        resposta = self.cliente("*").get("/api/livros", headers={"Origin": "http://localhost:8080"})
        self.assertEqual(resposta.headers["Access-Control-Allow-Origin"], "http://localhost:8080")


if __name__ == "__main__":
    unittest.main()
