# Biblioteca Gamer

Uma aplicação desktop moderna para gerenciar a sua coleção de jogos e consoles — rápida, fácil e expansível.

✨ Funcionalidades

Cadastro de consoles/plataformas com validação automática.

Cadastro, edição e remoção de jogos, associando ao console, status, nota, ano, gênero, favoritos e mais.

Listagem interativa do acervo com visual moderno (temas claro/escuro), filtros dinâmicos (por favorito, busca por nome, etc.).

Marcação de favoritos com estrela na Dreamview.

Barra de progresso exibindo jogos finalizados vs. total cadastrado.

Tema visual personalizável: troque entre temas escuros e claros com apenas 1 clique.

Mensagens visuais, tooltips e ícones nos botões para melhor usabilidade.

Duplo clique para editar rapidamente dados de um jogo.

## Como rodar

Pré-requisitos:

Python 3.10+ instalado (baixe de https://python.org/)

pip (já incluso normalmente)

1. Clone o projeto:

git clone https://github.com/KawanVictor/Biblioteca_Gamer.git

cd biblioteca_gamer

2. Instale as dependências:

pip install -r requirements.txt

3. Execute o app:

python main.py

💡 IMPORTANTE: Cadastre ao menos um console antes de adicionar jogos.

# Como Usar

No menu principal, escolha:

Consoles/Plataformas: cadastre ou remova plataformas (ex: PC, Xbox, PS5...).

Jogos: cadastre novos jogos, filtre por console, status e listas, busque pelo nome, edite com duplo clique na linha (ou "Editar selecionado") e remova com "Remover selecionado".

Use o botão "Alternar Tema" para trocar entre modos escuro/claro.

Marque favoritos para ver a estrela na tabela.

Barra de progresso mostra quantos jogos já zerou (conta os jogos com status "Zerado").

# Tecnologias Utilizadas

Python 3.10+

Tkinter com ttkbootstrap (interface estilizada)

SQLite (persistência local e leve)

Pillow (manipulação de imagens/ícones)
