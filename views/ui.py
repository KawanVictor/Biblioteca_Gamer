"""
Interface (Tkinter + ttkbootstrap): cria a janela, registra as telas e os atalhos globais.
Cada tela fica em um módulo próprio e é uma função que redesenha a janela principal.
"""

import os
import tkinter as tk

import ttkbootstrap as tb

from controllers import controller as ctl
from views import base
from views.base import TEMA_PADRAO, TEMAS
from views.consoles import tela_consoles
from views.estatisticas import tela_estatisticas
from views.jogos import tela_jogos
from views.menu import menu_principal

base.telas.update(menu=menu_principal, consoles=tela_consoles, jogos=tela_jogos, estatisticas=tela_estatisticas)


def atalho_novo_jogo():
    # na tela de jogos abre o formulário direto; em qualquer outra, vai para ela antes
    base.atalhos_tela["novo"]() if "novo" in base.atalhos_tela else tela_jogos(abrir_novo=True)


def iniciar():
    tema = ctl.ler_config("tema", TEMA_PADRAO)
    base.root = tb.Window(title="Biblioteca Gamer", themename=tema if tema in TEMAS else TEMA_PADRAO,
        size=(1040, 680), minsize=(960, 560))
    try:
        base.root.iconbitmap(default=base.recurso(os.path.join("assets", "icone.ico")))
    except tk.TclError:
        pass  # sem o arquivo do ícone o app usa o padrão
    base.root.place_window_center()
    base.root.bind_all('<Control-n>', base.atalho_global(atalho_novo_jogo))
    base.root.bind_all('<Control-q>', base.atalho_global(base.root.destroy))
    base.root.bind_all('<Control-m>', base.atalho_global(menu_principal))
    base.root.bind_all('<Control-f>', base.atalho_global(lambda: base.atalhos_tela.get("buscar", lambda: None)()))
    menu_principal()
    base.root.mainloop()
    ctl.fazer_backup()  # ao fechar, por qualquer caminho (botão Sair, Ctrl+Q ou o X da janela)
