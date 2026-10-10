"""
Menu principal, ranking de favoritos e troca de tema.
"""

import ttkbootstrap as tb
from ttkbootstrap.constants import DANGER, INFO, PRIMARY, SECONDARY, SUCCESS, WARNING

from controllers import controller as ctl
from views import base
from views.base import TEMA_PADRAO, TEMAS


def barra_progresso(frm):
    zerados, total = ctl.resumo_progresso()
    if total > 0:
        tb.Meter(frm, bootstyle=SUCCESS, subtext="Zerados", amountused=zerados, amounttotal=total,
            textfont="Arial 10 bold", stripethickness=7, metersize=150).pack(pady=8)


def exibe_ranking_favoritos():
    popup = tb.Toplevel(master=base.root, title="Top 5 Jogos Favoritos", resizable=(False, False))
    popup.transient(base.root)
    corpo = tb.Frame(popup, padding=16); corpo.pack(fill="both", expand=True)
    tb.Label(corpo, text="⭐ TOP 5 Favoritos", font=("Arial", 13, "bold")).pack(pady=(0, 8))
    top5 = ctl.ranking_favoritos()
    if not top5:
        tb.Label(corpo, text="Nenhum favorito ainda.\nMarque jogos com ⭐ para vê-los aqui.", justify="center").pack()
    for posicao, jogo in enumerate(top5, start=1):
        nota = f"Nota: {jogo['avaliacao']}" if jogo["avaliacao"] is not None else "sem nota"
        tb.Label(corpo, text=f"{posicao}. {jogo['nome']} ({jogo['console'] or '-'}) — {nota}").pack(anchor="w", pady=2)
    tb.Button(corpo, text="Fechar", bootstyle=SECONDARY, command=popup.destroy).pack(pady=(12, 0))
    popup.bind("<Escape>", lambda e: popup.destroy())
    popup.place_window_center()


def alternar_tema():
    atual = base.root.style.theme.name
    novo = TEMAS[(TEMAS.index(atual) + 1) % len(TEMAS)] if atual in TEMAS else TEMA_PADRAO
    base.root.style.theme_use(novo)
    ctl.gravar_config("tema", novo)


def menu_principal():
    base.limpar_frame()
    frm = tb.Frame(base.root)
    frm.pack(fill="both", expand=True)
    tb.Label(frm, text="🎮 Biblioteca Gamer", font=('Arial', 22, 'bold')).pack(pady=16)
    tb.Button(frm, text="Consoles/Plataformas", width=25, bootstyle=PRIMARY, command=lambda: base.ir_para("consoles")).pack(pady=6)
    tb.Button(frm, text="Jogos", width=25, bootstyle=SUCCESS, command=lambda: base.ir_para("jogos")).pack(pady=6)
    tb.Button(frm, text="Estatísticas", width=25, bootstyle=INFO, command=lambda: base.ir_para("estatisticas")).pack(pady=6)
    tb.Button(frm, text="Ver Ranking Favoritos", width=25, bootstyle=WARNING, command=exibe_ranking_favoritos).pack(pady=6)
    tb.Button(frm, text="Sair", width=25, bootstyle=DANGER, command=base.root.destroy).pack(pady=10)
    tb.Button(frm, text="Alternar Tema", bootstyle=SECONDARY, command=alternar_tema).pack(pady=4)
    barra_progresso(frm)
    tb.Label(frm, text="Ctrl+N novo jogo   •   Ctrl+M menu   •   Ctrl+Q sair", bootstyle=SECONDARY).pack(side="bottom", pady=8)
