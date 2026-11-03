# Livraria: Back-end (Exercício 8.6)

Camada **servidor** da arquitetura Cliente-Servidor da livraria: uma API REST em JSON, publicada separadamente do front-end.

- **Back-end publicado:** https://engsoft-lab86-backend.azurewebsites.net *(após o deploy)* (teste: https://engsoft-lab86-backend.azurewebsites.net/api/livros)
- **Front-end:** endereço do Azure Static Web Apps *(após o deploy)* · repositório [livraria-frontend-exercicio-8-6](https://github.com/HenriqueRSouza/livraria-frontend-exercicio-8-6)
- Diagrama da arquitetura: [board do Miro](https://miro.com/app/board/uXjVETAfWIY=/)

## Do diagrama para o código

| Diagrama | Código |
|---|---|
| Aplicação (app/servidor) | `app.py` + `livraria/servidor/app.py`: Flask, CORS e `/health` |
| Routes (rotas/endpoints) | `livraria/servidor/rotas.py`: API REST em `/api` |
| Negócios (regras) | `livraria/modulos/*/api.py`: catálogo, busca, usuários, estoque, pedidos, pagamentos, notificações |
| Dados (camada de dados) | `livraria/modulos/*/dados.py` + `livraria/compartilhado/repositorio_txt.py` |
| Banco de dados | pasta `LIVRARIA_DADOS`, um arquivo TXT por módulo (`/home/dados` no Azure) |

Os módulos de negócio vêm do monólito modular do exercício 8.3 e só falam entre si pela `api.py` de cada um ou por eventos.

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

Usei a porta 8000 porque, no macOS, a 5000 costuma estar ocupada pelo AirPlay. Variáveis: `LIVRARIA_DADOS` (pasta de dados, padrão `dados/`), `LIVRARIA_SECRET` e `LIVRARIA_CORS_ORIGENS`.

## Testes

```sh
.venv/bin/python -m unittest discover -v
```

- `tests/test_api.py`: C08–C10 pela API, login por token e CORS (inclusive preflight e respostas de erro).
- `tests/test_modulos.py`: C01–C07, C09, C10 na camada de negócios, eventos e saga.
- `tests/test_arquitetura.py`: camadas do servidor e fronteiras entre módulos.
- `tests/test_repositorio_txt.py`: camada de dados.

## Deploy (Azure App Service)

O workflow `.github/workflows/azure-webapp.yml` roda os testes e publica no Web App `engsoft-lab86-backend` a cada push na `main`. Ele usa o secret `AZURE_WEBAPP_PUBLISH_PROFILE` (perfil de publicação do Web App).

Configuração do Web App:

```sh
az webapp create -g <grupo> -p <plano> -n engsoft-lab86-backend --runtime "PYTHON:3.12"
az webapp config set -g <grupo> -n engsoft-lab86-backend --startup-file \
  'gunicorn --bind=0.0.0.0:8000 --workers 1 --threads 8 --timeout 120 app:app'
az webapp config appsettings set -g <grupo> -n engsoft-lab86-backend --settings \
  SCM_DO_BUILD_DURING_DEPLOYMENT=true LIVRARIA_DADOS=/home/dados \
  LIVRARIA_SECRET=<chave-aleatoria> LIVRARIA_CORS_ORIGENS=<endereço do front-end>
```

### Limites conhecidos

- Rode com **1 worker** (e várias threads): a saga de pedidos e o barramento de eventos ficam em memória.
- Cadastro sem senha, pagamento e notificações são **simulações** de demonstração.
