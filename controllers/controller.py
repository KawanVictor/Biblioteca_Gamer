"""
Controlador, repassa para o banco. Pronto para regras extras.
"""

from database.db import (
    cria_tabelas, cadastrar_console, buscar_consoles, remover_console,
    cadastrar_jogo, listar_jogos, remover_jogo, atualizar_jogo, ranking_favoritos
)

# Status possíveis de um jogo. A barra de progresso do menu conta os "Zerado".
STATUS_JOGO = ["Não iniciado", "Jogando", "Pausado", "Zerado", "Abandonado"]
STATUS_PADRAO = "Jogando"
