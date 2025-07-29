"""
controllers/controller.py
Controlador: faz a ponte entre view e banco, pronto para crescer com regras de negócio.
"""

from database.db import (
    cria_tabelas, cadastrar_console, buscar_consoles,
    remover_console, cadastrar_jogo, listar_jogos,
    remover_jogo, atualizar_jogo
)
# Pode adicionar funções que combinem ou validem regras de negócio futuramente.
