# Tarefas derivadas de livraria.md: Exercícios 8.3 (Monólito Modular), 8.5 (Cliente-Servidor) e 8.6 (Deploy)

Marcar somente após verificar a tarefa. T01–T17 foram concluídas nos exercícios 6 e 7.4 e são revalidadas na nova arquitetura.

- [x] T18 Atualizar a especificação com a arquitetura de monólito modular derivada do diagrama 8.2.
- [x] T19 Criar o núcleo compartilhado (erro, texto, barramento de eventos, repositório TXT genérico com trava entre processos).
- [x] T20 Separar os módulos catalogo, busca, usuarios, estoque, pedidos, pagamentos e notificacoes, cada um com api/dominio/dados e arquivo próprio (C01–C07, C09, C10).
- [x] T21 Substituir chamadas diretas por eventos onde há reação entre módulos; ligar tudo em `aplicacao.py`.
- [x] T22 Implementar a saga de reserva/compra com compensação de estoque.
- [x] T23 Criar o gateway/BFF (telas + `/health` + `/api/livros`) mantendo as URLs do 7.4 (C08).
- [x] T24 Testes de arquitetura: fronteiras entre módulos e um arquivo de dados por módulo.
- [x] T25 Preparar o deploy no Azure (gunicorn, Dockerfile, workflow do GitHub Actions) e documentar no README.

## Exercício 8.5 (Cliente-Servidor)

- [x] T26 Atualizar a especificação com a arquitetura Cliente-Servidor do diagrama (cliente MVC, servidor Aplicação/Routes/Negócios/Dados).
- [x] T27 Trocar as telas geradas no servidor por uma API REST em JSON (`/api`), com erros 400/401/404 e sessão por cookie.
- [x] T28 Criar o cliente JavaScript separado em Model (estado + HTTP), View (telas) e Controller (eventos/ações).
- [x] T29 Testar a API (C08–C10), as camadas do cliente e do servidor, e o fluxo completo do cliente contra o servidor.

## Exercício 8.6 (Deploy Cliente-Servidor)

- [x] T30 Separar front-end e back-end em repositórios próprios.
- [x] T31 Back-end: remover a entrega do cliente, liberar o front-end no CORS e trocar o cookie de sessão por token Bearer.
- [x] T32 Front-end: `config.js` com o endereço da API, token no `localStorage` e testes em Node (MVC, Model e View).
- [x] T33 Publicar o back-end no Azure App Service e o front-end em outro Web App (Node) no mesmo plano, ligados por LIVRARIA_API_URL e LIVRARIA_CORS_ORIGENS, com deploy automático pelo GitHub Actions.

## Exercício 10.2 (Banco SQL)

- [x] T34 Criar `RepositorioPostgres` e guardar usuários e favoritos no Azure Database for PostgreSQL: tabelas `clientes` (SERIAL, email UNIQUE) e `favoritos` (chave composta), transação com COMMIT/ROLLBACK.
- [x] T35 Escolher o banco por variável de ambiente (`LIVRARIA_POSTGRES_URL`); sem ela, os usuários continuam em TXT.
- [x] T36 Testar o repositório com banco real (serviço do GitHub Actions) e repetir C01–C10 com PostgreSQL.
- [x] T37 Publicar em Web Apps novos (`engsoft-lab10-backend` e `engsoft-lab10-frontend`) e cadastrar 4 usuários pela API.
