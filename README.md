# Livraria: Back-end (Exercícios 10.1 e 10.2)

Camada **servidor** da arquitetura Cliente-Servidor da livraria: uma API REST em JSON, publicada separadamente do front-end.

- **Exercício 10.1 (NoSQL):** o catálogo de livros fica no **Azure Cosmos DB for MongoDB**, com 12 livros cadastrados.
- **Exercício 10.2 (SQL):** os usuários (clientes e favoritos) ficam no **Azure Database for PostgreSQL**, com 4 usuários cadastrados.
- **Aplicação online (front-end):** https://engsoft-lab10-frontend.azurewebsites.net · repositório [livraria-frontend-exercicio-10](https://github.com/HenriqueRSouza/livraria-frontend-exercicio-10)
- **Back-end publicado:** https://engsoft-lab10-backend.azurewebsites.net (teste: https://engsoft-lab10-backend.azurewebsites.net/api/livros)
- Diagrama da arquitetura: [board do Miro](https://miro.com/app/board/uXjVETAfWIY=/)

## Do diagrama para o código

| Diagrama | Código |
|---|---|
| Aplicação (app/servidor) | `app.py` + `livraria/servidor/app.py`: Flask, CORS e `/health` |
| Routes (rotas/endpoints) | `livraria/servidor/rotas.py`: API REST em `/api` |
| Negócios (regras) | `livraria/modulos/*/api.py`: catálogo, busca, usuários, estoque, pedidos, pagamentos, notificações |
| Dados (camada de dados) | `livraria/modulos/*/dados.py` + `livraria/compartilhado/repositorio_*.py` |
| Banco NoSQL (catálogo) | Azure Cosmos DB for MongoDB: `RepositorioMongo` |
| Banco SQL (usuários) | Azure Database for PostgreSQL: `RepositorioPostgres` |
| Demais módulos | pasta `LIVRARIA_DADOS`, um arquivo TXT por módulo (`/home/dados` no Azure) |

Os módulos de negócio vêm do monólito modular do exercício 8.3 e só falam entre si pela `api.py` de cada um ou por eventos.

## Bancos de dados (Exercícios 10.1 e 10.2)

Todos os repositórios implementam a mesma interface `RepositorioModulo` (`listar`, `salvar`, `remover`, `transacao`). Por isso trocar o banco de um módulo só mexe no `dados.py` dele: as regras de negócio, as rotas e o front-end não mudaram.

```
Front-end (Node) ──HTTPS/JSON──▶ Back-end (Flask)
                                   ├─ catálogo ─────────▶ Azure Cosmos DB for MongoDB (NoSQL)
                                   ├─ usuários ─────────▶ Azure Database for PostgreSQL (SQL)
                                   └─ estoque, pedidos… ─▶ arquivos TXT em /home/dados
```

### Catálogo no Cosmos DB for MongoDB (NoSQL)

`livraria/compartilhado/repositorio_mongo.py` e `livraria/modulos/catalogo/dados.py`.

- Banco `livraria` (throughput compartilhado de 400 RU/s, dentro do free tier), uma coleção por entidade: `livro`, `edicao`, `promocao`, `avaliacao`.
- Cada registro é um documento com os campos do dataclass, por exemplo:
  ```json
  {"_id": 3, "id": 3, "titulo": "Dom Casmurro", "autor": "Machado de Assis", "genero": "Literatura", "sinopse": "..."}
  ```
- Ids novos (ex.: uma avaliação) saem da coleção `contadores` com `$inc` atômico.
- Na primeira execução, com o banco vazio, o back-end grava os **12 livros** de exemplo (com edições e promoções). Reiniciar não duplica.

### Usuários no PostgreSQL (SQL)

`livraria/compartilhado/repositorio_postgres.py` e `livraria/modulos/usuarios/dados.py`.

```sql
CREATE TABLE clientes (
    id SERIAL PRIMARY KEY, nome TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
    bairro TEXT NOT NULL, interesses TEXT[] NOT NULL DEFAULT '{}', criado_em TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE favoritos (
    cliente_id INTEGER NOT NULL REFERENCES clientes (id) ON DELETE CASCADE,
    livro_id INTEGER NOT NULL, PRIMARY KEY (cliente_id, livro_id));
```

- As tabelas são criadas na subida do back-end (`CREATE TABLE IF NOT EXISTS`).
- `transacao()` é uma transação real (COMMIT/ROLLBACK). O cadastro confere o email e insere o cliente na mesma transação, e o `UNIQUE` garante que não haja email repetido.
- `livro_id` não tem chave estrangeira porque o livro está em outro banco (MongoDB).
- Os 4 usuários foram cadastrados pela própria API (`POST /api/clientes`), como faria o front-end.

### Escolha do banco

| Variável | Efeito | Sem ela |
|---|---|---|
| `LIVRARIA_MONGO_URL` | string de conexão do Cosmos DB for MongoDB; o banco é o do caminho da URL ou `livraria` | catálogo em `catalogo.txt` |
| `LIVRARIA_POSTGRES_URL` | `postgresql://usuario:senha@servidor:5432/livraria?sslmode=require` | usuários em `usuarios.txt` |

As strings de conexão ficam só nas configurações do Web App, nunca no repositório.

## API REST

| Método e caminho | Uso | Login |
|---|---|---|
| `GET /api/livros?titulo=&autor=&genero=` | busca no catálogo | não |
| `GET /api/livros/<id>` | detalhes, edições, estoque por loja e avaliações | não |
| `GET /api/lojas?bairro=` | lojas por bairro | não |
| `POST /api/clientes` | cadastro; devolve `cliente` e `token` | não |
| `POST /api/sessao` | entrar pelo email; devolve `cliente` e `token` | não |
| `GET /api/sessao` | cliente do token (ou `null`) | opcional |
| `DELETE /api/sessao` | sair (o front-end apaga o token) | não |
| `GET /api/minha-area` | histórico, pontos, favoritos, recomendações, notificações e avaliações | sim |
| `PUT` / `DELETE /api/favoritos/<livro_id>` | salvar / remover favorito | sim |
| `POST /api/reservas` | reservar `{edicao_id, loja_id, cupom}` | sim |
| `POST /api/reservas/<codigo>/retirada` | retirar a reserva (vira compra) | sim |
| `POST /api/reservas/<codigo>/cancelamento` | cancelar a reserva | sim |
| `POST /api/compras` | compra direta `{edicao_id, loja_id, cupom}` | sim |
| `POST /api/alertas` | avisar quando repor `{edicao_id, loja_id}` | sim |
| `POST /api/estoque/reposicao` | reposição simulada (+1 unidade) | não |
| `PUT /api/livros/<id>/avaliacao` | avaliar `{nota, texto}` | sim |
| `GET /health` | verificação de saúde | não |

- **Login:** envie `Authorization: Bearer <token>`. O token é assinado com `LIVRARIA_SECRET` e vale 30 dias. Não há cookie, porque o front-end está em outro domínio.
- **Erros:** `{"erro": "mensagem"}` com 400 (404 em consultas). Sem login ou com token inválido: 401.
- **CORS:** só as origens de `LIVRARIA_CORS_ORIGENS` (separadas por vírgula) podem chamar a API pelo navegador. O padrão `*` libera qualquer uma, para desenvolvimento.

## Rodar localmente

Requer Python 3.10+.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py          # http://127.0.0.1:8000
```

Usei a porta 8000 porque, no macOS, a 5000 costuma estar ocupada pelo AirPlay. Variáveis: `LIVRARIA_DADOS` (pasta de dados, padrão `dados/`), `LIVRARIA_MONGO_URL`, `LIVRARIA_POSTGRES_URL`, `LIVRARIA_SECRET` e `LIVRARIA_CORS_ORIGENS`.

Para rodar com os bancos localmente, suba MongoDB e PostgreSQL em Docker:

```sh
docker run -d --name livraria-mongo -p 27017:27017 mongo:7
docker run -d --name livraria-pg -e POSTGRES_PASSWORD=teste -e POSTGRES_DB=livraria -p 5432:5432 postgres:16-alpine
LIVRARIA_MONGO_URL=mongodb://localhost:27017/livraria \
LIVRARIA_POSTGRES_URL=postgresql://postgres:teste@localhost:5432/livraria .venv/bin/python app.py
```

## Testes

```sh
.venv/bin/python -m unittest discover -v
# com os bancos (os containers acima):
LIVRARIA_TESTE_MONGO_URL=mongodb://localhost:27017/livraria_teste \
LIVRARIA_TESTE_POSTGRES_URL=postgresql://postgres:teste@localhost:5432/livraria \
  .venv/bin/python -m unittest discover -v
```

- `tests/test_bancos.py`: catálogo no MongoDB (12 livros, ids, upsert), usuários no PostgreSQL (SERIAL, UNIQUE, chave composta, ROLLBACK, 4 cadastros) e todos os critérios C01–C10 de novo com os dois bancos. No GitHub Actions, MongoDB e PostgreSQL sobem como serviços do workflow. Sem as variáveis, esses testes são pulados.

- `tests/test_api.py`: C08–C10 pela API, login por token e CORS (inclusive preflight e respostas de erro).
- `tests/test_modulos.py`: C01–C07, C09, C10 na camada de negócios, eventos e saga.
- `tests/test_arquitetura.py`: camadas do servidor e fronteiras entre módulos.
- `tests/test_repositorio_txt.py`: camada de dados.

## Deploy (Azure App Service)

O workflow `.github/workflows/azure-webapp.yml` roda os testes e publica no Web App `engsoft-lab10-backend` a cada push na `main`. Ele usa o secret `AZURE_WEBAPP_PUBLISH_PROFILE` (perfil de publicação do Web App).

Configuração do Web App:

```sh
az webapp create -g <grupo> -p <plano> -n engsoft-lab10-backend --runtime "PYTHON:3.12"
az webapp config set -g <grupo> -n engsoft-lab10-backend --startup-file \
  'gunicorn --bind=0.0.0.0:8000 --workers 1 --threads 8 --timeout 120 app:app'
az webapp config appsettings set -g <grupo> -n engsoft-lab10-backend --settings \
  SCM_DO_BUILD_DURING_DEPLOYMENT=true LIVRARIA_DADOS=/home/dados \
  LIVRARIA_MONGO_URL='<string de conexão do Cosmos DB>' \
  LIVRARIA_POSTGRES_URL='postgresql://<usuário>:<senha>@<servidor>.postgres.database.azure.com:5432/livraria?sslmode=require' \
  LIVRARIA_SECRET=<chave-aleatoria> \
  LIVRARIA_CORS_ORIGENS=https://engsoft-lab10-frontend.azurewebsites.net
```

O front-end é outro Web App (Node), que pode ficar no mesmo plano. Ele aponta para esta API pela variável `LIVRARIA_API_URL`, e esta API só aceita chamadas do navegador vindas das origens em `LIVRARIA_CORS_ORIGENS`.

Os bancos foram criados assim (o script completo está em `../deploy-azure-10.sh`, fora do repositório porque gera senhas):

```sh
az cosmosdb create -g <grupo> -n engsoft-lab10-livraria-mongo --kind MongoDB --server-version 4.2 --enable-free-tier true
az cosmosdb mongodb database create -g <grupo> -a engsoft-lab10-livraria-mongo -n livraria --throughput 400
az postgres flexible-server create -g <grupo> -n engsoft-lab10-livraria-pg --tier Burstable \
  --sku-name Standard_B1ms --version 16 --public-access 0.0.0.0   # 0.0.0.0 = só serviços do Azure
az postgres flexible-server db create -g <grupo> -s engsoft-lab10-livraria-pg -d livraria
```

### Limites conhecidos

- Rode com **1 worker** (e várias threads): a saga de pedidos e o barramento de eventos ficam em memória.
- Cadastro sem senha, pagamento e notificações são **simulações** de demonstração.
