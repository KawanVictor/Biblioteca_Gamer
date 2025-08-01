"""
Controlador, repassa para o banco. Pronto para regras extras.
"""

from database.db import (
    cria_tabelas, cadastrar_console, buscar_consoles, remover_console,
    cadastrar_jogo, listar_jogos, remover_jogo, atualizar_jogo, ranking_favoritos
)
