# Biblioteca Gamer

Uma aplicação desktop para gerenciar a sua coleção de jogos e consoles — rápida, fácil e expansível.

## ✨ Funcionalidades

- Cadastro, renomeação e remoção de consoles/plataformas.
- Cadastro, edição e remoção de jogos, com plataforma, status, nota, ano, gênero, datas, horas jogadas e comentários.
- Listas de favoritos ⭐, wishlist ❤️ e backlog 🔖.
- Tabela com busca por nome, filtros por plataforma, status e listas, e ordenação ao clicar no cabeçalho.
- Ranking dos 5 favoritos mais bem avaliados.
- Barra de progresso com os jogos zerados (a wishlist não entra na conta).
- Exportação e importação em CSV, para backup ou para abrir no Excel.
- Quatro temas visuais; o app lembra o último escolhido.

## Como rodar

Pré-requisitos: Python 3.10+ (https://python.org/) com pip.

1. Clone o projeto:

       git clone https://github.com/KawanVictor/Biblioteca_Gamer.git
       cd Biblioteca_Gamer

2. Instale as dependências (de preferência em um ambiente virtual):

       python -m venv venv
       venv\Scripts\activate
       pip install -r requirements.txt

3. Execute o app:

       python main.py

💡 Cadastre ao menos um console antes de adicionar jogos.

## Como usar

No menu principal, escolha:

- **Consoles/Plataformas:** cadastre plataformas (ex.: PC, Xbox, PS5...). Duplo clique renomeia; remover uma plataforma apaga também os jogos dela.
- **Jogos:** use "Novo jogo" para cadastrar. Duplo clique em uma linha (ou "Editar selecionado") abre o jogo para edição.
- **Alternar Tema:** troca entre os temas disponíveis.

Atalhos de teclado:

| Atalho | Ação |
| --- | --- |
| Ctrl+N | Novo jogo |
| Ctrl+F | Ir para a busca (tela de jogos) |
| Enter | Editar o jogo selecionado / salvar o formulário |
| Delete | Remover o item selecionado |
| Esc | Fechar o formulário |
| Ctrl+M | Voltar ao menu |
| Ctrl+Q | Sair |

## Seus dados

Os dados ficam no arquivo `biblioteca_gamer.db`, na pasta do projeto. Ele não é enviado para o GitHub, então faça backup pelo botão "Exportar CSV" da tela de jogos. "Importar CSV" lê o mesmo formato, cria as plataformas que faltarem e pula os jogos que já existem.

Ao abrir um banco criado por uma versão anterior do app, ele é atualizado automaticamente e uma cópia do original fica em `biblioteca_gamer.backup-v0.db`.

## Estrutura

- `main.py` — ponto de entrada.
- `views/ui.py` — telas.
- `controllers/controller.py` — validações, regras e CSV.
- `database/db.py` — esquema, migrações e consultas SQLite.
- `tests/` — testes automatizados. Rode com `python -m unittest` na raiz do projeto.

## Tecnologias

- Python 3.10+
- Tkinter com ttkbootstrap (interface estilizada)
- SQLite (persistência local e leve)
