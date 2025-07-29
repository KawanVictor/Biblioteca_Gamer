"""
Ponto de entrada do sistema (main.py).
Garante que banco está pronto e aciona a interface.
"""
from controllers.controller import cria_tabelas
from views.ui import iniciar

if __name__ == "__main__":
    cria_tabelas()
    iniciar()
