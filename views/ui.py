"""
Interface (Tkinter + ttkbootstrap). Cada tela é uma função que redesenha a janela principal.
"""

import csv
import tkinter as tk
from tkinter import filedialog

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox, Querybox
from ttkbootstrap.localization import MessageCatalog

from controllers import controller as ctl

root = None
atalhos_tela = {}  # atalhos que só valem na tela atual, ex.: {"buscar": função}

TEMAS = ["darkly", "cyborg", "solar", "journal"]
TEMA_PADRAO = "cyborg"

# (campo, título, largura, alinhamento) das colunas da tabela de jogos
COLUNAS_JOGOS = [
    ("nome", "Nome", 230, "w"), ("console", "Plataforma", 130, "center"), ("status", "Status", 110, "center"),
    ("avaliacao", "Nota", 55, "center"), ("favorito", "Fav", 45, "center"), ("wishlist", "Wishlist", 65, "center"),
    ("backlog", "Backlog", 65, "center"), ("ano_lancamento", "Ano", 55, "center"), ("horas_jogadas", "Horas", 55, "center"),
]
ICONES_LISTA = {"favorito": "⭐", "wishlist": "❤️", "backlog": "🔖"}


# ---------------------------------------------------------------- utilidades

def confirma(mensagem):
    # yesno devolve o texto (traduzido) do botão clicado, não um booleano
    return Messagebox.yesno(mensagem, title="Confirmar", parent=root) == MessageCatalog.translate("Yes")


def tooltip(widget, text):
    tip = tk.Toplevel(widget); tip.withdraw()
    tip.wm_overrideredirect(True)
    tk.Label(tip, text=text, background="#333", foreground="white", padx=6, pady=3).pack()
    def enter(e): tip.wm_geometry(f"+{widget.winfo_rootx()+20}+{widget.winfo_rooty()+40}"); tip.deiconify()
    def leave(e): tip.withdraw()
    widget.bind("<Enter>", enter); widget.bind("<Leave>", leave)


def limpar_frame():
    atalhos_tela.clear()
    for w in root.winfo_children():
        w.destroy()


def atalho_global(acao):
    """Atalho de teclado que é ignorado enquanto houver um diálogo aberto."""
    def tratar(evento):
        if root.grab_current() is None:
            acao()
    return tratar


def selecionado(tree, aviso):
    """Id (int) da linha selecionada, ou None depois de avisar que nada está selecionado."""
    sel = tree.selection()
    if not sel:
        Messagebox.show_warning(aviso, title="Aviso", parent=root)
        return None
    return int(sel[0])


# ---------------------------------------------------------------- menu principal

def barra_progresso(frm):
    zerados, total = ctl.resumo_progresso()
    if total > 0:
        tb.Meter(frm, bootstyle=SUCCESS, subtext="Zerados", amountused=zerados, amounttotal=total,
            textfont="Arial 10 bold", stripethickness=7, metersize=170).pack(pady=10)


def exibe_ranking_favoritos():
    popup = tb.Toplevel(master=root, title="Top 5 Jogos Favoritos", resizable=(False, False))
    popup.transient(root)
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
    atual = root.style.theme.name
    novo = TEMAS[(TEMAS.index(atual) + 1) % len(TEMAS)] if atual in TEMAS else TEMA_PADRAO
    root.style.theme_use(novo)
    ctl.gravar_config("tema", novo)


def menu_principal():
    limpar_frame()
    frm = tb.Frame(root)
    frm.pack(fill="both", expand=True)
    tb.Label(frm, text="🎮 Biblioteca Gamer", font=('Arial', 22, 'bold')).pack(pady=20)
    tb.Button(frm, text="Consoles/Plataformas", width=25, bootstyle=PRIMARY, command=tela_consoles).pack(pady=8)
    tb.Button(frm, text="Jogos", width=25, bootstyle=SUCCESS, command=tela_jogos).pack(pady=8)
    tb.Button(frm, text="Ver Ranking Favoritos", width=25, bootstyle=WARNING, command=exibe_ranking_favoritos).pack(pady=6)
    tb.Button(frm, text="Sair", width=25, bootstyle=DANGER, command=root.destroy).pack(pady=15)
    tb.Button(frm, text="Alternar Tema", bootstyle=SECONDARY, command=alternar_tema).pack(pady=4)
    barra_progresso(frm)
    tb.Label(frm, text="Ctrl+N novo jogo   •   Ctrl+M menu   •   Ctrl+Q sair", bootstyle=SECONDARY).pack(side="bottom", pady=10)


# ---------------------------------------------------------------- consoles

def tela_consoles():
    limpar_frame()
    frm = tb.LabelFrame(root, text="Cadastro e gerenciamento de plataformas/consoles", bootstyle=PRIMARY)
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
        idc = selecionado(tree, "Selecione uma plataforma!")
        if idc is None: return
        atual = tree.item(idc, "values")[0]
        novo = Querybox.get_string("Novo nome da plataforma:", title="Renomear", initialvalue=atual, parent=root)
        if novo is None or novo.strip() == atual: return
        try:
            ctl.salvar_console(novo, idc)
        except ctl.ErroValidacao as erro:
            feedback(str(erro), DANGER); return
        feedback(f"Plataforma renomeada para '{novo.strip()}'."); atualizar_lista()

    def acao_remover(evento=None):
        idc = selecionado(tree, "Selecione uma plataforma!")
        if idc is None: return
        nome, total = tree.item(idc, "values")
        total = int(total)
        pergunta = f"Remover a plataforma '{nome}'?"
        if total:
            pergunta += f"\n\nOs {total} jogos cadastrados nela também serão apagados." if total > 1 \
                else "\n\nO jogo cadastrado nela também será apagado."
        if confirma(pergunta):
            ctl.remover_console(idc); atualizar_lista(); feedback(f"Plataforma '{nome}' removida.")

    btn_cadastrar = tb.Button(linha_nome, text="Cadastrar", bootstyle=SUCCESS, command=acao_cadastrar)
    btn_cadastrar.pack(side="left", padx=(0, 5)); tooltip(btn_cadastrar, "Cadastrar nova plataforma (Enter)")
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
    btn_renomear.pack(side="left"); tooltip(btn_renomear, "Muda o nome da plataforma (ou duplo clique na linha)")
    btn_remover = tb.Button(rodape, text="Remover selecionada", bootstyle=DANGER, command=acao_remover)
    btn_remover.pack(side="left", padx=6); tooltip(btn_remover, "Remove a plataforma e todos os jogos nela (Delete)")
    tb.Button(rodape, text="Voltar ao menu", bootstyle=SECONDARY, command=menu_principal).pack(side="right")
    atualizar_lista()
    entry_console.focus_set()


# ---------------------------------------------------------------- jogos: formulário

def dialogo_jogo(consoles, jogo=None, ao_salvar=None):
    """Janela de cadastro (jogo=None) ou edição. ao_salvar(mensagem) é chamada depois de gravar."""
    dlg = tb.Toplevel(master=root, title="Editar jogo" if jogo else "Novo jogo", resizable=(False, False))
    dlg.transient(root)
    corpo = tb.Frame(dlg, padding=14); corpo.pack(fill="both", expand=True)
    ids_consoles = {c["nome"]: c["id"] for c in consoles}

    def valor(campo, padrao=""):
        return padrao if jogo is None or jogo[campo] is None else jogo[campo]

    def bloco(titulo, estilo, linha, coluna):
        frame = tb.LabelFrame(corpo, text=titulo, bootstyle=estilo, padding=8)
        frame.grid(row=linha, column=coluna, sticky="nsew", padx=6, pady=6)
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

    variaveis, datas = {}, {}

    dados = bloco("Dados do Jogo", INFO, 0, 0)
    entry_nome = campo_texto(dados, 0, "Nome*", "nome", 30)
    tb.Label(dados, text="Plataforma*").grid(row=1, column=0, sticky="w", pady=3)
    console_var = tk.StringVar(value=valor("console"))
    tb.Combobox(dados, textvariable=console_var, values=list(ids_consoles), state="readonly", width=28) \
        .grid(row=1, column=1, sticky="we", padx=(8, 0), pady=3)

    listas = bloco("Status & Listas", PRIMARY, 1, 0)
    tb.Label(listas, text="Status:").grid(row=0, column=0, sticky="w", pady=3)
    variaveis["status"] = tk.StringVar(value=valor("status", ctl.STATUS_PADRAO))
    tb.Combobox(listas, textvariable=variaveis["status"], values=ctl.STATUS_JOGO, state="readonly", width=18) \
        .grid(row=0, column=1, sticky="w", padx=(8, 0), pady=3)
    marcadores = tb.Frame(listas); marcadores.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
    for campo, rotulo, estilo in (("favorito", "Favorito ⭐", WARNING), ("wishlist", "Wishlist ❤️", INFO), ("backlog", "Backlog 🔖", PRIMARY)):
        variaveis[campo] = tk.IntVar(value=valor(campo, 0))
        tb.Checkbutton(marcadores, text=rotulo, variable=variaveis[campo], bootstyle=estilo).pack(side="left", padx=(0, 12))

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

    erro_var = tk.StringVar()
    tb.Label(corpo, textvariable=erro_var, bootstyle=DANGER).grid(row=2, column=0, columnspan=2, sticky="w", padx=6)

    def salvar(evento=None):
        campos = {campo: var.get() for campo, var in variaveis.items()}
        campos.update({campo: entry.get() for campo, entry in datas.items()})
        campos["id_console"] = ids_consoles.get(console_var.get())
        try:
            ctl.salvar_jogo(campos, jogo["id"] if jogo else None)
        except ctl.ErroValidacao as erro:
            erro_var.set(str(erro)); return
        nome = campos["nome"].strip()
        dlg.destroy()
        if ao_salvar:
            ao_salvar(f"Jogo '{nome}' atualizado!" if jogo else f"Jogo '{nome}' cadastrado!")

    botoes = tb.Frame(corpo); botoes.grid(row=3, column=0, columnspan=2, sticky="e", padx=6, pady=(8, 0))
    tb.Button(botoes, text="Cancelar", bootstyle=SECONDARY, command=dlg.destroy).pack(side="left", padx=6)
    tb.Button(botoes, text="Salvar alterações" if jogo else "Cadastrar jogo", bootstyle=SUCCESS, command=salvar).pack(side="left")
    dlg.bind("<Return>", salvar)
    dlg.bind("<Escape>", lambda e: dlg.destroy())
    dlg.place_window_center()
    dlg.wait_visibility()
    dlg.grab_set()  # modal: a tela de jogos fica bloqueada até salvar ou cancelar
    entry_nome.focus_set()
    return dlg


# ---------------------------------------------------------------- jogos: listagem

def valor_celula(jogo, campo):
    valor = jogo[campo]
    if campo in ICONES_LISTA:
        return ICONES_LISTA[campo] if valor else ""
    if campo in ("console", "status"):
        return valor or "-"
    return "" if valor is None else valor


def ordenar_jogos(jogos, campo, decrescente):
    """Ordena pela coluna; jogos sem valor nela ficam sempre no fim."""
    def chave(jogo):
        valor = jogo[campo]
        return valor.casefold() if isinstance(valor, str) else valor
    preenchidos = [j for j in jogos if j[campo] not in (None, "")]
    vazios = [j for j in jogos if j[campo] in (None, "")]
    return sorted(preenchidos, key=chave, reverse=decrescente) + vazios


def tela_jogos(abrir_novo=False):
    limpar_frame()
    frm = tb.Frame(root, padding=(20, 14)); frm.pack(fill="both", expand=True)
    consoles = ctl.buscar_consoles()
    ids_consoles = {c["nome"]: c["id"] for c in consoles}
    jogos_listados = {}  # id -> linha exibida na tabela
    ordem = {"campo": "nome", "decrescente": False}

    # --- barra de ações
    acoes = tb.Frame(frm); acoes.pack(fill="x")
    tb.Label(acoes, text="Jogos cadastrados", font=("Arial", 14, "bold")).pack(side="left")
    contador = tk.StringVar()
    tb.Label(acoes, textvariable=contador, bootstyle=SECONDARY).pack(side="left", padx=12)

    # --- filtros
    filtros = tb.Frame(frm); filtros.pack(fill="x", pady=(10, 4))
    busca_var = tk.StringVar(); f_console_var = tk.StringVar(value="Todas"); f_status_var = tk.StringVar(value="Todos")
    marcados = {campo: tk.IntVar() for campo in ICONES_LISTA}
    tb.Label(filtros, text="Buscar:").pack(side="left")
    entry_busca = tb.Entry(filtros, textvariable=busca_var, width=22)
    entry_busca.pack(side="left", padx=(4, 12))
    tb.Label(filtros, text="Plataforma:").pack(side="left")
    f_console = tb.Combobox(filtros, textvariable=f_console_var, values=["Todas"] + list(ids_consoles), state="readonly", width=16)
    f_console.pack(side="left", padx=(4, 12))
    tb.Label(filtros, text="Status:").pack(side="left")
    # status fora da lista fixa (bancos antigos) também entram no filtro, para poderem ser achados
    status_extras = [s for s in ctl.status_em_uso() if s not in ctl.STATUS_JOGO]
    f_status = tb.Combobox(filtros, textvariable=f_status_var, values=["Todos"] + ctl.STATUS_JOGO + status_extras, state="readonly", width=13)
    f_status.pack(side="left", padx=(4, 12))

    # --- rodapé e tabela (rodapé primeiro, para a tabela ocupar o espaço que sobrar)
    rodape = tb.Frame(frm); rodape.pack(side="bottom", fill="x", pady=(8, 0))
    msg = tk.StringVar()
    label_feedback = tb.Label(frm, textvariable=msg, bootstyle=SUCCESS); label_feedback.pack(side="bottom", anchor="w", pady=(4, 0))
    def feedback(texto, estilo=SUCCESS):
        label_feedback.config(bootstyle=estilo); msg.set(texto)
    area_tabela = tb.Frame(frm); area_tabela.pack(fill="both", expand=True, pady=3)
    tree = tb.Treeview(area_tabela, columns=[c[0] for c in COLUNAS_JOGOS], show="headings", bootstyle=INFO, selectmode="browse")
    for campo, titulo, largura, alinhamento in COLUNAS_JOGOS:
        tree.column(campo, width=largura, anchor=alinhamento)
    rolagem = tb.Scrollbar(area_tabela, orient="vertical", command=tree.yview); tree.configure(yscrollcommand=rolagem.set)
    rolagem.pack(side="right", fill="y"); tree.pack(side="left", fill="both", expand=True)

    def atualizar_listagem(*_):
        jogos = ctl.listar_jogos(
            filtro_console=ids_consoles.get(f_console_var.get()),
            filtro_status=None if f_status_var.get() == "Todos" else f_status_var.get(),
            apenas_favoritos=marcados["favorito"].get(), apenas_wishlist=marcados["wishlist"].get(),
            apenas_backlog=marcados["backlog"].get(), busca_nome=busca_var.get()
        )
        jogos = ordenar_jogos(jogos, ordem["campo"], ordem["decrescente"])
        selecionado_antes = tree.selection()
        jogos_listados.clear(); tree.delete(*tree.get_children())
        for jogo in jogos:
            jogos_listados[jogo["id"]] = jogo
            tree.insert("", "end", iid=jogo["id"], values=[valor_celula(jogo, c[0]) for c in COLUNAS_JOGOS])
        if selecionado_antes and tree.exists(selecionado_antes[0]):
            tree.selection_set(selecionado_antes[0])
        for campo, titulo, _, _ in COLUNAS_JOGOS:
            seta = (" ▼" if ordem["decrescente"] else " ▲") if campo == ordem["campo"] else ""
            tree.heading(campo, text=titulo + seta, command=lambda c=campo: ordenar_por(c))
        total = ctl.contar_jogos()
        contador.set(f"{len(jogos)} de {total} jogos" if len(jogos) != total else f"{total} jogos")

    def ordenar_por(campo):
        ordem["decrescente"] = not ordem["decrescente"] if ordem["campo"] == campo else False
        ordem["campo"] = campo
        atualizar_listagem()

    def limpar_filtros():
        busca_var.set(""); f_console_var.set("Todas"); f_status_var.set("Todos")
        for var in marcados.values(): var.set(0)
        atualizar_listagem()

    for campo, icone in ICONES_LISTA.items():
        chk = tb.Checkbutton(filtros, text=icone, variable=marcados[campo], command=atualizar_listagem)
        chk.pack(side="left", padx=4); tooltip(chk, f"Mostrar só {campo}")
    tb.Button(filtros, text="Limpar filtros", bootstyle=(SECONDARY, OUTLINE), command=limpar_filtros).pack(side="left", padx=(12, 0))
    busca_var.trace_add("write", atualizar_listagem)
    f_console.bind("<<ComboboxSelected>>", atualizar_listagem); f_status.bind("<<ComboboxSelected>>", atualizar_listagem)

    def apos_salvar(mensagem):
        atualizar_listagem(); feedback(mensagem)

    def acao_novo(evento=None):
        if not consoles:
            Messagebox.show_warning("Cadastre ao menos uma plataforma antes de adicionar jogos.", title="Aviso", parent=root); return
        dialogo_jogo(consoles, ao_salvar=apos_salvar)

    def acao_editar(evento=None):
        id_jogo = selecionado(tree, "Selecione um jogo na lista!")
        if id_jogo is not None:
            dialogo_jogo(consoles, jogos_listados[id_jogo], ao_salvar=apos_salvar)

    def acao_remover(evento=None):
        id_jogo = selecionado(tree, "Selecione um jogo na lista!")
        if id_jogo is None: return
        nome = jogos_listados[id_jogo]["nome"]
        if confirma(f"Remover o jogo '{nome}'?"):
            ctl.remover_jogo(id_jogo); atualizar_listagem(); feedback(f"Jogo '{nome}' removido.")

    def acao_exportar():
        caminho = filedialog.asksaveasfilename(parent=root, title="Exportar jogos", defaultextension=".csv",
            initialfile="biblioteca_gamer.csv", filetypes=[("CSV", "*.csv")])
        if not caminho: return
        try:
            total = ctl.exportar_csv(caminho)
        except OSError as erro:
            Messagebox.show_error(f"Não foi possível gravar o arquivo:\n{erro}", title="Erro", parent=root); return
        feedback(f"{total} jogos exportados para {caminho}")

    def acao_importar():
        caminho = filedialog.askopenfilename(parent=root, title="Importar jogos", filetypes=[("CSV", "*.csv")])
        if not caminho: return
        try:
            importados, duplicados, erros = ctl.importar_csv(caminho)
        except (OSError, UnicodeDecodeError, csv.Error, ctl.ErroValidacao) as erro:
            Messagebox.show_error(f"Não foi possível importar o arquivo:\n{erro}", title="Erro", parent=root); return
        resumo = f"{importados} jogos importados, {duplicados} já existiam."
        if erros:
            detalhes = "\n".join(erros[:10]) + (f"\n... e mais {len(erros) - 10}." if len(erros) > 10 else "")
            Messagebox.show_warning(f"{resumo}\n\n{len(erros)} linhas foram ignoradas:\n{detalhes}", title="Importação", parent=root)
        tela_jogos()  # redesenha: a importação pode ter criado plataformas
        atalhos_tela["feedback"](resumo)

    def duplo_clique(evento):
        if tree.identify_row(evento.y): acao_editar()
    tree.bind("<Double-1>", duplo_clique)
    tree.bind("<Return>", acao_editar)
    tree.bind("<Delete>", acao_remover)

    btn_novo = tb.Button(rodape, text="Novo jogo", bootstyle=SUCCESS, command=acao_novo)
    btn_novo.pack(side="left"); tooltip(btn_novo, "Cadastrar um jogo (Ctrl+N)")
    btn_editar = tb.Button(rodape, text="Editar selecionado", bootstyle=INFO, command=acao_editar)
    btn_editar.pack(side="left", padx=6); tooltip(btn_editar, "Abre o jogo para edição (Enter ou duplo clique na linha)")
    btn_remover = tb.Button(rodape, text="Remover selecionado", bootstyle=DANGER, command=acao_remover)
    btn_remover.pack(side="left"); tooltip(btn_remover, "Remove o jogo selecionado (Delete)")
    tb.Button(rodape, text="Voltar ao menu", bootstyle=SECONDARY, command=menu_principal).pack(side="right")
    btn_importar = tb.Button(rodape, text="Importar CSV", bootstyle=(SECONDARY, OUTLINE), command=acao_importar)
    btn_importar.pack(side="right", padx=6); tooltip(btn_importar, "Adiciona os jogos de um CSV exportado pelo app")
    btn_exportar = tb.Button(rodape, text="Exportar CSV", bootstyle=(SECONDARY, OUTLINE), command=acao_exportar)
    btn_exportar.pack(side="right"); tooltip(btn_exportar, "Salva uma cópia de todos os jogos (backup / Excel)")

    atalhos_tela.update(buscar=entry_busca.focus_set, novo=acao_novo, feedback=feedback)
    atualizar_listagem()
    if abrir_novo:
        acao_novo()


# ---------------------------------------------------------------- inicialização

def atalho_novo_jogo():
    # na tela de jogos abre o formulário direto; em qualquer outra, vai para ela antes
    atalhos_tela["novo"]() if "novo" in atalhos_tela else tela_jogos(abrir_novo=True)


def iniciar():
    global root
    tema = ctl.ler_config("tema", TEMA_PADRAO)
    root = tb.Window(title="Biblioteca Gamer", themename=tema if tema in TEMAS else TEMA_PADRAO,
        size=(1000, 680), minsize=(900, 560))
    root.place_window_center()
    root.bind_all('<Control-n>', atalho_global(atalho_novo_jogo))
    root.bind_all('<Control-q>', atalho_global(root.destroy))
    root.bind_all('<Control-m>', atalho_global(menu_principal))
    root.bind_all('<Control-f>', atalho_global(lambda: atalhos_tela.get("buscar", lambda: None)()))
    menu_principal()
    root.mainloop()
