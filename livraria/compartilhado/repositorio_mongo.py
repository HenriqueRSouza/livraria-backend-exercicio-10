"""RepositorioMongo: implementa RepositorioModulo guardando os registros de UM módulo em um banco MongoDB.

Usado pelo catálogo com o Azure Cosmos DB for MongoDB (Exercício 10.1). Cada entidade vira uma coleção
(livro, edicao, promocao, avaliacao) e cada registro vira um documento com os mesmos campos do dataclass:
    {"_id": 3, "id": 3, "titulo": "Dom Casmurro", "autor": "Machado de Assis", ...}

Os ids novos saem da coleção "contadores" ($inc atômico no servidor), então dois pedidos simultâneos
nunca recebem o mesmo id. Cada gravação é atômica por documento; transacao() serializa as operações
compostas dentro do processo (o servidor roda com 1 worker).
"""
import threading
from contextlib import contextmanager
from dataclasses import asdict

from pymongo import MongoClient, ReturnDocument

from livraria.compartilhado.repositorio import RepositorioModulo

CONTADORES = "contadores"


class RepositorioMongo(RepositorioModulo):
    def __init__(self, url, tipos, chaves=None, dados_iniciais=(), banco_padrao="livraria"):
        """url: string de conexão (o banco vem do caminho da URL, ou banco_padrao);
        chaves: campos que identificam registros sem "id"."""
        self.cliente = MongoClient(url, retryWrites=False, serverSelectionTimeoutMS=10000)
        self.banco = self.cliente.get_default_database(banco_padrao)
        self.tipos = {classe.__name__.lower(): classe for classe in tipos}
        self.chaves = chaves or {}
        self.trava = threading.RLock()
        self._semear(dados_iniciais)

    def listar(self, tipo):
        documentos = self.banco[self._colecao(tipo)].find({}, {"_id": 0})
        registros = [tipo(**doc) for doc in documentos]
        return sorted(registros, key=lambda r: self._chave(r))

    def salvar(self, registro):
        with self.transacao():
            if self._campos(type(registro)) == ("id",) and registro.id == 0:
                registro.id = self._proximo_id(type(registro))
            self.banco[self._colecao(type(registro))].replace_one(
                {"_id": self._id_documento(registro)}, self._documento(registro), upsert=True)
            return registro

    def remover(self, registro):
        with self.transacao():
            self.banco[self._colecao(type(registro))].delete_one({"_id": self._id_documento(registro)})

    @contextmanager
    def transacao(self):
        with self.trava:
            yield

    def fechar(self):
        self.cliente.close()

    def _semear(self, dados_iniciais):
        """Grava os dados de exemplo só se o banco do módulo estiver vazio (reiniciar não duplica)."""
        with self.trava:
            if any(self.banco[nome].count_documents({}, limit=1) for nome in self.tipos):
                return
            for registro in dados_iniciais:
                self.salvar(registro)
                if self._campos(type(registro)) == ("id",):
                    self.banco[CONTADORES].update_one({"_id": self._colecao(type(registro))},
                                                      {"$max": {"valor": registro.id}}, upsert=True)

    def _proximo_id(self, tipo):
        contador = self.banco[CONTADORES].find_one_and_update(
            {"_id": self._colecao(tipo)}, {"$inc": {"valor": 1}}, upsert=True, return_document=ReturnDocument.AFTER)
        return contador["valor"]

    def _colecao(self, tipo):
        return tipo.__name__.lower()

    def _campos(self, tipo):
        return self.chaves.get(tipo, ("id",))

    def _chave(self, registro):
        return tuple(getattr(registro, c) for c in self._campos(type(registro)))

    def _id_documento(self, registro):
        chave = self._chave(registro)
        return chave[0] if len(chave) == 1 else "-".join(str(c) for c in chave)

    def _documento(self, registro):
        return {"_id": self._id_documento(registro), **asdict(registro)}
