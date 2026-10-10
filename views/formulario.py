"""
Formulário de cadastro e edição de jogo, com a busca de dados na Steam e a capa.
"""

import tkinter as tk
from tkinter import filedialog

import ttkbootstrap as tb
from ttkbootstrap.constants import DANGER, INFO, OUTLINE, PRIMARY, SECONDARY, SUCCESS, WARNING
from ttkbootstrap.tooltip import ToolTip

from controllers import controller as ctl
from views import base

CAPA_FORMULARIO = (130, 195)
TIPOS_IMAGEM = [("Imagens", "*.jpg *.jpeg *.png *.webp *.bmp *.gif")]


def escolher_jogo_steam(janela_pai, achados):
    """Mostra os jogos encontrados na Steam e espera a escolha. Devolve o item escolhido ou None."""
    escolha = []
    dlg = tb.Toplevel(master=janela_pai, title="Qual destes é o jogo?", resizable=(False, False))
    dlg.transient(janela_pai)
    corpo = tb.Frame(dlg, padding=12); corpo.pack(fill="both", expand=True)
    lista = tb.Treeview(corpo, columns=("nome",), show="", selectmode="browse", height=min(len(achados), 10))
    lista.column("nome", width=360)
    for indice, item in enumerate(achados):
        lista.insert("", "end", iid=indice, values=(item["nome"],))
    lista.selection_set(0); lista.pack()
    def confirmar(evento=None):
        escolha.append(achados[int(lista.selection()[0])]); dlg.destroy()
    botoes = tb.Frame(corpo); botoes.pack(anchor="e", pady=(10, 0))
    tb.Button(botoes, text="Cancelar", bootstyle=SECONDARY, command=dlg.destroy).pack(side="left", padx=6)
    tb.Button(botoes, text="Usar este", bootstyle=SUCCESS, command=confirmar).pack(side="left")
    lista.bind("<Double-1>", confirmar); dlg.bind("<Return>", confirmar); dlg.bind("<Escape>", lambda e: dlg.destroy())
    dlg.place_window_center(); dlg.wait_visibility(); dlg.grab_set(); lista.focus_set()
    janela_pai.wait_window(dlg)
    janela_pai.grab_set()
    return escolha[0] if escolha else None


def dialogo_jogo(consoles, jogo=None, ao_salvar=None):
    """Janela de cadastro (jogo=None) ou edição. ao_salvar(mensagem) é chamada depois de gravar."""
    dlg = tb.Toplevel(master=base.root, title="Editar jogo" if jogo else "Novo jogo", resizable=(False, False))
    dlg.transient(base.root)
    corpo = tb.Frame(dlg, padding=14); corpo.pack(fill="both", expand=True)
    ids_consoles = {c["nome"]: c["id"] for c in consoles}
    variaveis, datas = {}, {}
    # capa["nova"]: imagem escolhida ou baixada (caminho ou bytes), gravada só ao salvar o jogo
    capa = {"nova": None, "remover": False}

    def valor(campo, padrao=""):
        return padrao if jogo is None or jogo[campo] is None else jogo[campo]

    def bloco(titulo, estilo, linha, coluna, linhas=1):
        frame = tb.LabelFrame(corpo, text=titulo, bootstyle=estilo, padding=8)
        frame.grid(row=linha, column=coluna, rowspan=linhas, sticky="nsew", padx=6, pady=6)
        frame.columnconfigure(1, weight=1)
        return frame

    def campo_texto(frame, linha, rotulo, campo, largura):
        var = tk.StringVar(value=str(valor(campo)))
        tb.Label(frame, text=rotulo).grid(row=linha, column=0, sticky="w", pady=3)
        entry = tb.Entry(frame, textvariable=var, width=largura)
        entry.grid(row=linha, column=1, sticky="w" if largura < 20 else "we", padx=(8, 0), pady=3)
        variaveis[campo] = var
        return entry

    def campo_data(frame, linha, rotulo, campo):
        tb.Label(frame, text=rotulo).grid(row=linha, column=0, sticky="w", pady=3)
        seletor = tb.DateEntry(frame, dateformat="%d/%m/%Y", width=12)
        seletor.grid(row=linha, column=1, sticky="w", padx=(8, 0), pady=3)
        seletor.entry.delete(0, "end")  # a data é opcional: começa vazia em vez de "hoje"
        seletor.entry.insert(0, ctl.data_para_br(valor(campo)))
        datas[campo] = seletor.entry

    aviso_var = tk.StringVar()
    label_aviso = tb.Label(corpo, textvariable=aviso_var, bootstyle=DANGER)
    label_aviso.grid(row=2, column=0, columnspan=3, sticky="w", padx=6)
    def aviso(texto, estilo=DANGER):
        label_aviso.config(bootstyle=estilo); aviso_var.set(texto)

    # --- dados básicos
    dados = bloco("Dados do Jogo", INFO, 0, 0)
    entry_nome = campo_texto(dados, 0, "Nome*", "nome", 30)
    tb.Label(dados, text="Plataforma*").grid(row=1, column=0, sticky="w", pady=3)
    console_var = tk.StringVar(value=valor("console"))
    tb.Combobox(dados, textvariable=console_var, values=list(ids_consoles), state="readonly", width=28) \
        .grid(row=1, column=1, sticky="we", padx=(8, 0), pady=3)
    variaveis["steam_appid"] = tk.StringVar(value=str(valor("steam_appid")))

    # --- status e listas
    listas = bloco("Status & Listas", PRIMARY, 1, 0)
    tb.Label(listas, text="Status:").grid(row=0, column=0, sticky="w", pady=3)
    variaveis["status"] = tk.StringVar(value=valor("status", ctl.STATUS_PADRAO))
    tb.Combobox(listas, textvariable=variaveis["status"], values=ctl.STATUS_JOGO, state="readonly", width=18) \
        .grid(row=0, column=1, sticky="w", padx=(8, 0), pady=3)
    marcadores = tb.Frame(listas); marcadores.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
    for campo, rotulo, estilo in (("favorito", "Favorito ⭐", WARNING), ("wishlist", "Wishlist ❤️", INFO), ("backlog", "Backlog 🔖", PRIMARY)):
        variaveis[campo] = tk.IntVar(value=valor(campo, 0))
        tb.Checkbutton(marcadores, text=rotulo, variable=variaveis[campo], bootstyle=estilo).pack(side="left", padx=(0, 12))

    # --- extras e progresso
    extras = bloco("Extras", SECONDARY, 0, 1)
    campo_texto(extras, 0, "Avaliação (1-10):", "avaliacao", 6)
    campo_texto(extras, 1, "Ano lançamento:", "ano_lancamento", 8)
    campo_texto(extras, 2, "Gênero:", "genero", 26)
    campo_texto(extras, 3, "Comentário:", "comentario", 26)
    progresso = bloco("Progresso", SUCCESS, 1, 1)
    campo_data(progresso, 0, "Data início:", "data_inicio")
    campo_data(progresso, 1, "Data fim:", "data_fim")
    campo_texto(progresso, 2, "Horas jogadas:", "horas_jogadas", 6)
    campo_texto(progresso, 3, "Progresso/Notas:", "progresso", 26)

    # --- capa
    quadro_capa = bloco("Capa", SECONDARY, 0, 2, linhas=2)
    label_capa = tb.Label(quadro_capa, text="Sem capa", anchor="center", width=18)
    label_capa.grid(row=0, column=0, columnspan=2, pady=(0, 8), ipady=4)
    label_capa.image = None
    quadro_capa.rowconfigure(0, weight=1)
    if jogo and ctl.tem_capa(jogo["id"]):
        base.mostrar_capa(label_capa, ctl.caminho_capa(jogo["id"]), CAPA_FORMULARIO)

    def usar_capa(imagem):
        if not base.mostrar_capa(label_capa, imagem, CAPA_FORMULARIO):
            return False
        capa.update(nova=imagem, remover=False)
        return True

    def escolher_capa():
        caminho = filedialog.askopenfilename(parent=dlg, title="Escolher capa", filetypes=TIPOS_IMAGEM)
        if caminho and not usar_capa(caminho):
            aviso("O arquivo escolhido não é uma imagem válida.")

    def tirar_capa():
        base.mostrar_capa(label_capa, None, CAPA_FORMULARIO)
        capa.update(nova=None, remover=True)

    def buscar_na_steam():
        aviso("")
        try:
            achados = base.com_espera(dlg, lambda: ctl.buscar_na_steam(variaveis["nome"].get()))
            if not achados:
                aviso("Nenhum jogo com esse nome foi encontrado na Steam."); return
            escolhido = achados[0] if len(achados) == 1 else escolher_jogo_steam(dlg, achados)
            if escolhido is None: return
            achado = base.com_espera(dlg, lambda: ctl.dados_da_steam(escolhido["appid"]))
        except ctl.ErroSteam as erro:
            aviso(str(erro)); return
        # só preenche o que está vazio: o que o usuário digitou não é sobrescrito
        variaveis["steam_appid"].set(str(escolhido["appid"]))
        if not variaveis["ano_lancamento"].get().strip() and achado["ano"]:
            variaveis["ano_lancamento"].set(str(achado["ano"]))
        if not variaveis["genero"].get().strip():
            variaveis["genero"].set(achado["genero"])
        if achado["capa"] and label_capa.image is None:
            usar_capa(achado["capa"])
        aviso(f"Dados preenchidos a partir de '{escolhido['nome']}'.", SUCCESS)

    btn_steam = tb.Button(dados, text="Buscar dados na Steam", bootstyle=(INFO, OUTLINE), command=buscar_na_steam)
    btn_steam.grid(row=2, column=1, sticky="e", pady=(6, 0))
    ToolTip(btn_steam, "Preenche ano, gênero e capa pelo nome do jogo (precisa de internet)")
    tb.Button(quadro_capa, text="Escolher...", bootstyle=(SECONDARY, OUTLINE), command=escolher_capa).grid(row=1, column=0, sticky="we", padx=(0, 3))
    tb.Button(quadro_capa, text="Remover", bootstyle=(SECONDARY, OUTLINE), command=tirar_capa).grid(row=1, column=1, sticky="we", padx=(3, 0))
    quadro_capa.columnconfigure(0, weight=1)

    def salvar(evento=None):
        campos = {campo: var.get() for campo, var in variaveis.items()}
        campos.update({campo: entry.get() for campo, entry in datas.items()})
        campos["id_console"] = ids_consoles.get(console_var.get())
        try:
            id_jogo = ctl.salvar_jogo(campos, jogo["id"] if jogo else None)
            if capa["nova"]:
                ctl.salvar_capa(id_jogo, capa["nova"])
            elif capa["remover"]:
                ctl.remover_capa(id_jogo)
        except ctl.ErroValidacao as erro:
            aviso(str(erro)); return
        nome = campos["nome"].strip()
        dlg.destroy()
        if ao_salvar:
            ao_salvar(f"Jogo '{nome}' atualizado!" if jogo else f"Jogo '{nome}' cadastrado!")

    botoes = tb.Frame(corpo); botoes.grid(row=3, column=0, columnspan=3, sticky="e", padx=6, pady=(8, 0))
    tb.Button(botoes, text="Cancelar", bootstyle=SECONDARY, command=dlg.destroy).pack(side="left", padx=6)
    tb.Button(botoes, text="Salvar alterações" if jogo else "Cadastrar jogo", bootstyle=SUCCESS, command=salvar).pack(side="left")
    dlg.bind("<Return>", salvar)
    dlg.bind("<Escape>", lambda e: dlg.destroy())
    dlg.place_window_center()
    dlg.wait_visibility()
    dlg.grab_set()  # modal: a tela de jogos fica bloqueada até salvar ou cancelar
    entry_nome.focus_set()
    return dlg
