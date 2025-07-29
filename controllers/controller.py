"""
Controller central (controllers/controller.py).
Orquestra ações entre os módulos de interface (views) e banco (database).
No exemplo, apenas importações simples para repassar funções.
"""

from database.db import (
    cria_tabelas,
    cadastrar_console, buscar_consoles, remover_console,
    cadastrar_jogo, listar_jogos, remover_jogo, atualizar_jogo
)

# Opcional: Adicione aqui funções de validação mais complexas, automatização, etc.
