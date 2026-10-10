"""
Tela de consoles/plataformas.
"""

import tkinter as tk

import ttkbootstrap as tb
from ttkbootstrap.constants import DANGER, INFO, PRIMARY, SECONDARY, SUCCESS
from ttkbootstrap.dialogs import Querybox
from ttkbootstrap.tooltip import ToolTip

from controllers import controller as ctl
from views import base


def tela_consoles():
    base.limpar_frame()
    frm = tb.LabelFrame(base.root, text="Cadastro e gerenciamento de plataformas/consoles", bootstyle=PRIMARY)
    frm.pack(fill="both", expand=True, padx=20, pady=20, ipadx=8, ipady=8)
    tb.Label(frm, text="Nome da plataforma*", font=("Arial", 11, "bold")).pack(anchor="w", pady=(4, 0))
    nome_var = tk.StringVar()
    linha_nome = tb.Frame(frm); linha_nome.pack(fill="x", pady=4)
    entry_console = tb.Entry(linha_nome, textvariable=nome_var, bootstyle=INFO)
    entry_console.pack(side="left", fill="x", expand=True, padx=(5, 8))
    msg = tk.StringVar(value="")
    label_feedback = tb.Label(frm, textvariable=msg, bootstyle=SUCCESS)
    def feedback(texto, estilo=SUCCESS):
        label_feedback.config(bootstyle=estilo); msg.set(texto)

    def atualizar_lista():
        tree.delete(*tree.get_children())
        for console in ctl.buscar_consoles():
            tree.insert("", "end", iid=console["id"], values=(console["nome"], console["total_jogos"]))

    def acao_cadastrar(evento=None):
        try:
            ctl.salvar_console(nome_var.get())
        except ctl.ErroValidacao as erro:
            feedback(str(erro), DANGER); return
        feedback(f"Plataforma '{nome_var.get().strip()}' cadastrada!"); nome_var.set(""); atualizar_lista()

    def acao_renomear(evento=None):
        idc = base.selecionado(tree, "Selecione uma plataforma!")
        if idc is None: return
        atual = tree.item(idc, "values")[0]
        novo = Querybox.get_string("Novo nome da plataforma:", title="Renomear", initialvalue=atual, parent=base.root)
        if novo is None or novo.strip() == atual: return
        try:
            ctl.salvar_console(novo, idc)
        except ctl.ErroValidacao as erro:
            feedback(str(erro), DANGER); return
        feedback(f"Plataforma renomeada para '{novo.strip()}'."); atualizar_lista()

    def acao_remover(evento=None):
        idc = base.selecionado(tree, "Selecione uma plataforma!")
        if idc is None: return
        nome, total = tree.item(idc, "values")
        total = int(total)
        pergunta = f"Remover a plataforma '{nome}'?"
        if total:
            pergunta += f"\n\nOs {total} jogos cadastrados nela também serão apagados." if total > 1 \
                else "\n\nO jogo cadastrado nela também será apagado."
        if base.confirma(pergunta):
            ctl.remover_console(idc); atualizar_lista(); feedback(f"Plataforma '{nome}' removida.")

    btn_cadastrar = tb.Button(linha_nome, text="Cadastrar", bootstyle=SUCCESS, command=acao_cadastrar)
    btn_cadastrar.pack(side="left", padx=(0, 5)); ToolTip(btn_cadastrar, "Cadastrar nova plataforma (Enter)")
    entry_console.bind("<Return>", acao_cadastrar)
    label_feedback.pack(anchor="w", pady=(2, 7))
    tb.Separator(frm, orient="horizontal").pack(fill="x", pady=8)
    tb.Label(frm, text="Plataformas cadastradas:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(5, 2))
    rodape = tb.Frame(frm); rodape.pack(side="bottom", fill="x", pady=(8, 0))
    tree = tb.Treeview(frm, columns=("Nome", "Jogos"), show="headings", bootstyle=PRIMARY, selectmode="browse")
    tree.heading("Nome", text="Nome"); tree.column("Nome", width=300, anchor="w")
    tree.heading("Jogos", text="Jogos"); tree.column("Jogos", width=80, anchor="center")
    tree.pack(fill="both", expand=True, pady=4)
    tree.bind("<Double-1>", lambda e: acao_renomear() if tree.identify_row(e.y) else None)
    tree.bind("<Delete>", acao_remover)
    btn_renomear = tb.Button(rodape, text="Renomear selecionada", bootstyle=INFO, command=acao_renomear)
    btn_renomear.pack(side="left"); ToolTip(btn_renomear, "Muda o nome da plataforma (ou duplo clique na linha)")
    btn_remover = tb.Button(rodape, text="Remover selecionada", bootstyle=DANGER, command=acao_remover)
    btn_remover.pack(side="left", padx=6); ToolTip(btn_remover, "Remove a plataforma e todos os jogos nela (Delete)")
    tb.Button(rodape, text="Voltar ao menu", bootstyle=SECONDARY, command=lambda: base.ir_para("menu")).pack(side="right")
    atualizar_lista()
    entry_console.focus_set()
