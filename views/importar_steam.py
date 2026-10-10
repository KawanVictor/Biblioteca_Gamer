"""
Diálogo que importa a biblioteca de uma conta Steam.
"""

import tkinter as tk

import ttkbootstrap as tb
from ttkbootstrap.constants import DANGER, SECONDARY, SUCCESS

from controllers import controller as ctl
from controllers.steam import PAGINA_CHAVE
from views import base


def dialogo_steam(consoles, ao_concluir):
    """Pede a chave da API e o SteamID e importa a biblioteca da conta. ao_concluir(mensagem) roda no fim."""
    dlg = tb.Toplevel(master=base.root, title="Importar biblioteca da Steam", resizable=(False, False))
    dlg.transient(base.root)
    corpo = tb.Frame(dlg, padding=16); corpo.pack(fill="both", expand=True)
    corpo.columnconfigure(1, weight=1)
    nomes = [c["nome"] for c in consoles]
    chave_var = tk.StringVar(value=ctl.ler_chave_steam())
    id_var = tk.StringVar(value=ctl.ler_config("steam_id", ""))
    console_var = tk.StringVar(value="PC" if "PC" in nomes else nomes[0])
    tb.Label(corpo, justify="left", wraplength=430, text=(
        "Traz todos os jogos da sua conta com as horas jogadas. Jogos que já estão na plataforma "
        "escolhida não são duplicados: só as horas são atualizadas.\n\n"
        f"• Chave da API: crie a sua em {PAGINA_CHAVE}\n"
        "• SteamID: os 17 números do endereço do seu perfil (steamID64)\n"
        "• No perfil, a privacidade de 'Detalhes dos jogos' precisa estar como público"
    )).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))
    tb.Label(corpo, text="Chave da API:").grid(row=1, column=0, sticky="w", pady=4)
    entry_chave = tb.Entry(corpo, textvariable=chave_var, show="•", width=40)
    entry_chave.grid(row=1, column=1, sticky="we", padx=(8, 0), pady=4)
    tb.Label(corpo, text="SteamID:").grid(row=2, column=0, sticky="w", pady=4)
    tb.Entry(corpo, textvariable=id_var, width=40).grid(row=2, column=1, sticky="we", padx=(8, 0), pady=4)
    tb.Label(corpo, text="Importar para:").grid(row=3, column=0, sticky="w", pady=4)
    tb.Combobox(corpo, textvariable=console_var, values=nomes, state="readonly").grid(row=3, column=1, sticky="we", padx=(8, 0), pady=4)
    erro_var = tk.StringVar()
    tb.Label(corpo, textvariable=erro_var, bootstyle=DANGER, wraplength=430, justify="left").grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))

    def importar(evento=None):
        id_console = next(c["id"] for c in consoles if c["nome"] == console_var.get())
        try:
            novos, atualizados = base.com_espera(dlg, lambda: ctl.importar_steam(chave_var.get(), id_var.get(), id_console))
        except ctl.ErroSteam as erro:
            erro_var.set(str(erro)); return
        dlg.destroy()
        ao_concluir(f"Steam: {novos} jogos novos, {atualizados} atualizados.")

    botoes = tb.Frame(corpo); botoes.grid(row=5, column=0, columnspan=2, sticky="e", pady=(12, 0))
    tb.Button(botoes, text="Cancelar", bootstyle=SECONDARY, command=dlg.destroy).pack(side="left", padx=6)
    tb.Button(botoes, text="Importar", bootstyle=SUCCESS, command=importar).pack(side="left")
    dlg.bind("<Return>", importar); dlg.bind("<Escape>", lambda e: dlg.destroy())
    dlg.place_window_center(); dlg.wait_visibility(); dlg.grab_set(); entry_chave.focus_set()
    return dlg
