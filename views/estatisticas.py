"""
Tela de estatísticas do acervo.
"""

import ttkbootstrap as tb
from ttkbootstrap.constants import DANGER, INFO, PRIMARY, SECONDARY, SUCCESS, WARNING

from controllers import controller as ctl
from views import base


def tela_estatisticas():
    base.limpar_frame()
    frm = tb.Frame(base.root, padding=(20, 14)); frm.pack(fill="both", expand=True)
    topo = tb.Frame(frm); topo.pack(fill="x")
    tb.Label(topo, text="Estatísticas", font=("Arial", 14, "bold")).pack(side="left")
    tb.Button(topo, text="Voltar ao menu", bootstyle=SECONDARY, command=lambda: base.ir_para("menu")).pack(side="right")
    dados = ctl.estatisticas()
    if dados["jogos"] == 0:
        tb.Label(frm, text="Cadastre jogos para ver as estatísticas aqui.", bootstyle=SECONDARY).pack(pady=40)
        return

    def numero(valor):
        return f"{valor:,}".replace(",", ".")
    def nota(valor):
        return "-" if valor is None else f"{valor:.1f}".replace(".", ",")

    resumo = tb.Frame(frm); resumo.pack(fill="x", pady=(12, 8))
    percentual = round(100 * dados["zerados"] / dados["jogos"])
    cartoes = [
        ("Jogos no acervo", numero(dados["jogos"]), PRIMARY), ("Horas jogadas", numero(dados["horas"]), INFO),
        ("Nota média", nota(dados["nota_media"]), WARNING), ("Zerados", f"{dados['zerados']} ({percentual}%)", SUCCESS),
        ("Backlog", numero(dados["backlog"]), SECONDARY), ("Wishlist", numero(dados["wishlist"]), DANGER),
    ]
    for coluna, (titulo, valor, estilo) in enumerate(cartoes):
        cartao = tb.LabelFrame(resumo, text=titulo, bootstyle=estilo, padding=(10, 4))
        cartao.grid(row=0, column=coluna, sticky="nsew", padx=4)
        tb.Label(cartao, text=valor, font=("Arial", 16, "bold")).pack()
        resumo.columnconfigure(coluna, weight=1, uniform="cartao")

    grade = tb.Frame(frm); grade.pack(fill="both", expand=True)
    def tabela(posicao, titulo, colunas, linhas):
        """colunas: lista de (título, largura). A primeira coluna é alinhada à esquerda."""
        quadro = tb.LabelFrame(grade, text=titulo, padding=6)
        quadro.grid(row=posicao // 3, column=posicao % 3, sticky="nsew", padx=4, pady=4)
        tree = tb.Treeview(quadro, columns=[c[0] for c in colunas], show="headings", height=5, selectmode="none")
        for indice, (nome, largura) in enumerate(colunas):
            tree.heading(nome, text=nome); tree.column(nome, width=largura, anchor="w" if indice == 0 else "center")
        for linha in linhas:
            tree.insert("", "end", values=linha)
        tree.pack(fill="both", expand=True)
    for indice in range(3):
        grade.columnconfigure(indice, weight=1, uniform="tabela")
    grade.rowconfigure(0, weight=1); grade.rowconfigure(1, weight=1)

    tabela(0, "Por status", [("Status", 150), ("Jogos", 60)],
        [(r["status"], r["jogos"]) for r in dados["por_status"]])
    tabela(1, "Por plataforma", [("Plataforma", 120), ("Jogos", 50), ("Horas", 60)],
        [(r["console"], r["jogos"], numero(r["horas"])) for r in dados["por_plataforma"]])
    tabela(2, "Zerados por ano", [("Ano", 100), ("Jogos", 60)],
        [(r["ano"], r["jogos"]) for r in dados["zerados_por_ano"]])
    tabela(3, "Gêneros mais comuns", [("Gênero", 130), ("Jogos", 50), ("Nota", 50)],
        [(r["genero"], r["jogos"], nota(r["nota_media"])) for r in dados["por_genero"]])
    tabela(4, "Mais jogados", [("Jogo", 150), ("Horas", 60)],
        [(r["nome"], numero(r["horas"])) for r in dados["mais_jogados"]])
    tb.Label(grade, justify="left", bootstyle=SECONDARY, wraplength=260, text=(
        "A wishlist não entra nos números do acervo.\n\n"
        "'Zerados por ano' usa a data de fim dos jogos com status Zerado."
    )).grid(row=1, column=2, sticky="nw", padx=10, pady=14)
