import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.localization import MessageCatalog
from controllers.controller import *

root = None

def confirma(mensagem):
    # yesno devolve o texto (traduzido) do botão clicado, não um booleano
    return Messagebox.yesno(mensagem, title="Confirmar", parent=root) == MessageCatalog.translate("Yes")

def int_ou_none(texto, campo, minimo=None, maximo=None):
    """Campo numérico opcional: vazio vira None; inválido lança ValueError com a mensagem pronta."""
    texto = texto.strip()
    if not texto: return None
    try: valor = int(texto)
    except ValueError: raise ValueError(f"{campo} deve ser um número inteiro.")
    if minimo is not None and valor < minimo: raise ValueError(f"{campo} não pode ser menor que {minimo}.")
    if maximo is not None and valor > maximo: raise ValueError(f"{campo} não pode ser maior que {maximo}.")
    return valor

def tooltip(widget, text):
    tip = tk.Toplevel(widget); tip.withdraw()
    tip.wm_overrideredirect(True)
    label = tk.Label(tip, text=text, background="#333", foreground="white", padx=6, pady=3); label.pack()
    def enter(e): tip.wm_geometry(f"+{widget.winfo_rootx()+20}+{widget.winfo_rooty()+40}"); tip.deiconify()
    def leave(e): tip.withdraw()
    widget.bind("<Enter>", enter); widget.bind("<Leave>", leave)

def carregar_icone(nome_arquivo, tamanho=(20,20)):
    try: img = Image.open(f"imagens/{nome_arquivo}").resize(tamanho); return ImageTk.PhotoImage(img)
    except: return None

def limpar_frame(): [w.destroy() for w in root.winfo_children()]

def barra_progresso(frm):
    todos = listar_jogos()
    total = len(todos)
    zerados = sum(1 for r in todos if r[3] and "zerad" in r[3].lower())
    if total > 0:
        tb.Meter(frm, bootstyle=SUCCESS, subtext="Zerados", amountused=zerados, amounttotal=total,
            textfont="Arial 10 bold", stripethickness=7).pack(pady=10)

def exibe_ranking_favoritos():
    popup = tb.Toplevel(root)
    popup.title("Top 5 Jogos Favoritos")
    top5 = ranking_favoritos()
    tb.Label(popup, text="⭐ TOP 5 Favoritos", font=("Arial", 13, "bold")).pack()
    for nome, console, nota in top5:
        tb.Label(popup, text=f"{nome} ({console}) — Nota: {nota}").pack(anchor='w', padx=8, pady=2)

def menu_principal():
    limpar_frame()
    frm = tb.Frame(root)
    frm.pack(fill="both", expand=True)
    tk.Label(frm, text="🎮 Biblioteca Gamer", font=('Arial', 22, 'bold')).pack(pady=20)
    tb.Button(frm, text="Consoles/Plataformas", width=25, bootstyle=PRIMARY, command=tela_consoles).pack(pady=8)
    tb.Button(frm, text="Jogos", width=25, bootstyle=SUCCESS, command=tela_jogos).pack(pady=8)
    tb.Button(frm, text="Ver Ranking Favoritos", width=25, bootstyle=WARNING, command=exibe_ranking_favoritos).pack(pady=6)
    tb.Button(frm, text="Sair", width=25, bootstyle=DANGER, command=root.destroy).pack(pady=15)
    temas = ["darkly", "cyborg", "solar", "journal"]
    def alternar_tema():
        atual = root.style.theme.name; idx = (temas.index(atual)+1)%len(temas) if atual in temas else 0; root.style.theme_use(temas[idx])
    tb.Button(frm, text="Alternar Tema", bootstyle=SECONDARY, command=alternar_tema).pack(pady=4)
    barra_progresso(frm)
    root.bind_all('<Control-n>', lambda e: tela_jogos())
    root.bind_all('<Control-q>', lambda e: root.destroy())
    root.bind_all('<Control-m>', lambda e: menu_principal())

def tela_consoles():
    limpar_frame()
    frm = tb.LabelFrame(root, text="Cadastro e gerenciamento de plataformas/consoles", bootstyle=PRIMARY)
    frm.pack(fill="x", padx=20, pady=20, ipadx=8, ipady=8)
    tb.Label(frm, text="Nome da plataforma*", font=("Arial", 11, "bold")).pack(anchor="w", pady=(4,0))
    nome_var = tk.StringVar()
    entry_console = tb.Entry(frm, textvariable=nome_var, width=30, bootstyle=INFO)
    entry_console.pack(fill="x", padx=5, pady=4)
    msg = tk.StringVar(value=""); label_feedback = tb.Label(frm, textvariable=msg, bootstyle=SUCCESS); label_feedback.pack(anchor="w", pady=(2,7))
    def acao_cadastrar():
        nome = nome_var.get().strip()
        if not nome:
            label_feedback.config(bootstyle=DANGER); msg.set("Preencha o nome da plataforma."); return
        if cadastrar_console(nome):
            label_feedback.config(bootstyle=SUCCESS); msg.set(f"Plataforma '{nome}' cadastrada!"); nome_var.set(""); atualizar_lista()
        else:
            label_feedback.config(bootstyle=DANGER); msg.set("Nome já existe ou inválido.")
    btn_cadastrar = tb.Button(frm, text="Cadastrar", bootstyle=SUCCESS, command=acao_cadastrar)
    btn_cadastrar.pack(pady=8); tooltip(btn_cadastrar, "Cadastrar nova plataforma")
    tb.Separator(frm, orient="horizontal").pack(fill="x", pady=8)
    tb.Label(frm, text="Plataformas cadastradas:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(5,2))
    tree = tb.Treeview(frm, columns=("ID", "Nome"), show="headings", bootstyle=PRIMARY)
    tree.heading("ID", text="ID"); tree.column("ID", width=50)
    tree.heading("Nome", text="Nome"); tree.column("Nome", width=200)
    tree.pack(fill="x", pady=4)
    def atualizar_lista():
        tree.delete(*tree.get_children())
        for id_console, nome in buscar_consoles():
            tree.insert("", "end", iid=id_console, values=(id_console, nome))
    def remover_sel():
        sel = tree.selection()
        if not sel:
            Messagebox.show_warning("Selecione uma plataforma!", title="Aviso", parent=root); return
        idc = int(sel[0])
        if confirma("Remover plataforma também apagará os jogos associados. Continuar?"):
            remover_console(idc); atualizar_lista(); msg.set("Plataforma removida.")
    btn_remover = tb.Button(frm, text="Remover selecionada", bootstyle=DANGER, command=remover_sel)
    btn_remover.pack(pady=(0,8)); tooltip(btn_remover, "Remove a plataforma e todos os jogos nela")
    voltar = tb.Button(frm, text="Voltar ao menu", bootstyle=SECONDARY, command=menu_principal)
    voltar.pack(); atualizar_lista()

def tela_jogos():
    limpar_frame()
    frm = tb.Frame(root); frm.pack(fill="both", expand=True, padx=25, pady=17)
    consoles = buscar_consoles(); nomes_consoles = [nome for _, nome in consoles]
    sem_console = "Escolha a plataforma..."
    editando = {"id": None}  # id do jogo carregado no formulário; None = cadastro novo
    jogos_listados = {}      # id -> linha de listar_jogos() exibida na tabela
    # Formulário em duas colunas
    form = tb.Frame(frm); form.pack(fill="x")
    form.columnconfigure(0, weight=1); form.columnconfigure(1, weight=1)
    # Bloco dados básicos
    bloco_dados = tb.LabelFrame(form, text="Dados do Jogo", bootstyle=INFO); bloco_dados.grid(row=0, column=0, sticky="nsew", padx=8, pady=6)
    nome_var = tk.StringVar()
    tb.Label(bloco_dados, text="Nome*", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", pady=3)
    entry_nome = tb.Entry(bloco_dados, textvariable=nome_var, width=28, bootstyle=PRIMARY)
    entry_nome.grid(row=0, column=1, padx=6, pady=3)
    tb.Label(bloco_dados, text="Plataforma*", font=("Arial", 11, "bold")).grid(row=1, column=0, sticky="w")
    console_var = tk.StringVar(value=sem_console)
    combo = tb.Combobox(bloco_dados, textvariable=console_var, values=nomes_consoles, font=("Arial", 10), bootstyle=PRIMARY, width=25,
        state="readonly" if nomes_consoles else "disabled")
    combo.grid(row=1, column=1, padx=6, pady=3)
    tooltip(combo, "Selecione uma plataforma cadastrada")
    bloco_dados.columnconfigure(1, weight=1)
    # Bloco status/listas
    bloco_status = tb.LabelFrame(form, text="Status & Listas", bootstyle=PRIMARY); bloco_status.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
    status_var = tk.StringVar(value=STATUS_PADRAO); favorito_var = tk.IntVar(); wishlist_var = tk.IntVar(); backlog_var = tk.IntVar()
    tb.Label(bloco_status, text="Status:").grid(row=0, column=0, sticky="w")
    tb.Combobox(bloco_status, textvariable=status_var, values=STATUS_JOGO, state="readonly", width=18).grid(row=0, column=1, padx=3, pady=2, sticky="w")
    tb.Checkbutton(bloco_status, text="Favorito ⭐", variable=favorito_var, bootstyle=WARNING).grid(row=1, column=0)
    tb.Checkbutton(bloco_status, text="Wishlist ❤️", variable=wishlist_var, bootstyle=INFO).grid(row=1, column=1)
    tb.Checkbutton(bloco_status, text="Backlog 🔖", variable=backlog_var, bootstyle=PRIMARY).grid(row=1, column=2)
    bloco_status.columnconfigure(1, weight=1)
    # Bloco extras (campos numéricos são StringVar: vazio é permitido e a conversão é validada ao salvar)
    bloco_extras = tb.LabelFrame(form, text="Extras", bootstyle=SECONDARY); bloco_extras.grid(row=0, column=1, sticky="nsew", padx=8, pady=6)
    avaliacao_var = tk.StringVar(); ano_var = tk.StringVar(); genero_var = tk.StringVar(); comentario_var = tk.StringVar()
    tb.Label(bloco_extras, text="Avaliação (1-10):").grid(row=0, column=0, sticky="w")
    tb.Entry(bloco_extras, textvariable=avaliacao_var, width=6).grid(row=0, column=1, padx=2, sticky="w")
    tb.Label(bloco_extras, text="Ano lançamento:").grid(row=1, column=0, sticky="w")
    tb.Entry(bloco_extras, textvariable=ano_var, width=8).grid(row=1, column=1, padx=2, sticky="w")
    tb.Label(bloco_extras, text="Gênero:").grid(row=2, column=0, sticky="w")
    tb.Entry(bloco_extras, textvariable=genero_var, width=18).grid(row=2, column=1, padx=2, sticky="w")
    tb.Label(bloco_extras, text="Comentário:").grid(row=3, column=0, sticky="w")
    tb.Entry(bloco_extras, textvariable=comentario_var, width=22).grid(row=3, column=1, padx=2, sticky="we")
    bloco_extras.columnconfigure(1, weight=1)
    # Bloco progresso
    bloco_progresso = tb.LabelFrame(form, text="Progresso", bootstyle=SUCCESS); bloco_progresso.grid(row=1, column=1, sticky="nsew", padx=8, pady=4)
    data_ini_var = tk.StringVar(); data_fim_var = tk.StringVar(); horas_var = tk.StringVar(); progresso_var = tk.StringVar()
    tb.Label(bloco_progresso, text="Data início (DD/MM/AAAA):").grid(row=0, column=0, sticky="w")
    tb.Entry(bloco_progresso, textvariable=data_ini_var, width=12).grid(row=0, column=1, padx=2, sticky="w")
    tb.Label(bloco_progresso, text="Data fim:").grid(row=1, column=0, sticky="w")
    tb.Entry(bloco_progresso, textvariable=data_fim_var, width=12).grid(row=1, column=1, padx=2, sticky="w")
    tb.Label(bloco_progresso, text="Horas jogadas:").grid(row=2, column=0, sticky="w")
    tb.Entry(bloco_progresso, textvariable=horas_var, width=6).grid(row=2, column=1, padx=2, sticky="w")
    tb.Label(bloco_progresso, text="Progresso/Notas:").grid(row=3, column=0, sticky="w")
    tb.Entry(bloco_progresso, textvariable=progresso_var, width=30).grid(row=3, column=1, padx=2, sticky="we")
    bloco_progresso.columnconfigure(1, weight=1)
    # feedback
    msg = tk.StringVar(value=""); label_feedback = tb.Label(frm, textvariable=msg, bootstyle=SUCCESS); label_feedback.pack(anchor="w", pady=(2,0))
    def feedback(texto, estilo=SUCCESS): label_feedback.config(bootstyle=estilo); msg.set(texto)
    def limpar_form():
        editando["id"] = None
        nome_var.set(""); console_var.set(sem_console); status_var.set(STATUS_PADRAO); avaliacao_var.set("")
        comentario_var.set(""); favorito_var.set(0); ano_var.set(""); genero_var.set("")
        wishlist_var.set(0); backlog_var.set(0); data_ini_var.set(""); data_fim_var.set("")
        horas_var.set(""); progresso_var.set("")
        btn_salvar.config(text="Cadastrar jogo"); btn_cancelar.config(state="disabled")
    def acao_salvar():
        nome = nome_var.get().strip()
        if not nome:
            feedback("Preencha o nome do jogo.", DANGER); return
        id_console = next((cid for cid, nome_c in consoles if nome_c == console_var.get()), None)
        if id_console is None:
            feedback("Escolha uma plataforma cadastrada.", DANGER); return
        try:
            avaliacao = int_ou_none(avaliacao_var.get(), "Avaliação", 1, 10)
            ano = int_ou_none(ano_var.get(), "Ano de lançamento", 0)
            horas = int_ou_none(horas_var.get(), "Horas jogadas", 0)
        except ValueError as e:
            feedback(str(e), DANGER); return
        dados = (
            nome, id_console, status_var.get(), avaliacao, comentario_var.get(),
            favorito_var.get(), ano, genero_var.get(),
            wishlist_var.get(), backlog_var.get(), data_ini_var.get(), data_fim_var.get(), horas, progresso_var.get()
        )
        if editando["id"] is None:
            cadastrar_jogo(*dados); texto = f"Jogo '{nome}' cadastrado!"
        else:
            atualizar_jogo(editando["id"], *dados); texto = f"Jogo '{nome}' atualizado!"
        limpar_form(); feedback(texto); atualizar_listagem()
    def acao_cancelar(): limpar_form(); feedback("")
    barra_acoes = tb.Frame(frm); barra_acoes.pack(fill="x", pady=(8,4), padx=10)
    btn_salvar = tb.Button(barra_acoes, text="Cadastrar jogo", bootstyle=SUCCESS, command=acao_salvar)
    btn_salvar.pack(side="right")
    tooltip(btn_salvar, "Salvar os dados do formulário")
    btn_cancelar = tb.Button(barra_acoes, text="Cancelar edição", bootstyle=SECONDARY, command=acao_cancelar, state="disabled")
    btn_cancelar.pack(side="right", padx=6)
    # --- Listagem com filtros
    sep = tb.Separator(frm, orient="horizontal"); sep.pack(fill="x", padx=5, pady=6)
    tb.Label(frm, text="Jogos cadastrados", font=("Arial", 12, "bold")).pack(anchor="w")
    filtros = tb.Frame(frm); filtros.pack(fill="x", padx=10, pady=(4,2))
    busca_var = tk.StringVar(); f_console_var = tk.StringVar(value="Todas"); f_status_var = tk.StringVar(value="Todos")
    f_fav_var = tk.IntVar(); f_wish_var = tk.IntVar(); f_back_var = tk.IntVar()
    tb.Label(filtros, text="Buscar:").pack(side="left")
    tb.Entry(filtros, textvariable=busca_var, width=22).pack(side="left", padx=(4,12))
    tb.Label(filtros, text="Plataforma:").pack(side="left")
    f_console = tb.Combobox(filtros, textvariable=f_console_var, values=["Todas"] + nomes_consoles, state="readonly", width=16)
    f_console.pack(side="left", padx=(4,12))
    tb.Label(filtros, text="Status:").pack(side="left")
    f_status = tb.Combobox(filtros, textvariable=f_status_var, values=["Todos"] + STATUS_JOGO, state="readonly", width=13)
    f_status.pack(side="left", padx=(4,12))
    # Rodapé antes da tabela para ela ocupar o espaço que sobrar
    rodape = tb.Frame(frm); rodape.pack(side="bottom", fill="x", pady=(7,2), padx=9)
    area_tabela = tb.Frame(frm); area_tabela.pack(fill="both", expand=True, padx=10, pady=3)
    cols = ("ID", "Nome", "Plataforma", "Status", "Nota", "Fav", "Wishlist", "Backlog", "Ano")
    tree = tb.Treeview(area_tabela, columns=cols, show="headings", bootstyle=INFO, selectmode="browse", height=6)
    for col in cols:
        tree.heading(col, text=col); tree.column(col, width=70, anchor="center")
    tree.column("Nome", width=240, anchor="w"); tree.column("Plataforma", width=130); tree.column("Status", width=110)
    rolagem = tb.Scrollbar(area_tabela, orient="vertical", command=tree.yview); tree.configure(yscrollcommand=rolagem.set)
    rolagem.pack(side="right", fill="y"); tree.pack(side="left", fill="both", expand=True)
    def atualizar_listagem(*_):
        id_console = next((cid for cid, nome_c in consoles if nome_c == f_console_var.get()), None)
        status = f_status_var.get() if f_status_var.get() in STATUS_JOGO else None
        jogos = listar_jogos(
            filtro_console=id_console, filtro_status=status, apenas_favoritos=f_fav_var.get(),
            apenas_wishlist=f_wish_var.get(), apenas_backlog=f_back_var.get(), busca_nome=busca_var.get()
        )
        jogos_listados.clear(); tree.delete(*tree.get_children())
        for r in jogos:
            jogos_listados[r[0]] = r
            tree.insert("", "end", iid=r[0], values=(
                r[0], r[1], r[2] or "-", r[3] or "-", r[4] if r[4] is not None else "",
                "⭐" if r[5] else "", "❤️" if r[6] else "", "🔖" if r[7] else "", r[12] or ""
            ))
    tb.Checkbutton(filtros, text="⭐", variable=f_fav_var, bootstyle=WARNING, command=atualizar_listagem).pack(side="left", padx=4)
    tb.Checkbutton(filtros, text="❤️", variable=f_wish_var, bootstyle=INFO, command=atualizar_listagem).pack(side="left", padx=4)
    tb.Checkbutton(filtros, text="🔖", variable=f_back_var, bootstyle=PRIMARY, command=atualizar_listagem).pack(side="left", padx=4)
    busca_var.trace_add("write", atualizar_listagem)
    f_console.bind("<<ComboboxSelected>>", atualizar_listagem); f_status.bind("<<ComboboxSelected>>", atualizar_listagem)
    def jogo_selecionado():
        sel = tree.selection()
        if not sel:
            Messagebox.show_warning("Selecione um jogo na lista!", title="Aviso", parent=root); return None
        return jogos_listados[int(sel[0])]
    def acao_editar():
        r = jogo_selecionado()
        if r is None: return
        txt = lambda v: "" if v is None else str(v)
        editando["id"] = r[0]
        nome_var.set(r[1]); console_var.set(r[2] if r[2] in nomes_consoles else sem_console); status_var.set(r[3] or STATUS_PADRAO)
        avaliacao_var.set(txt(r[4])); favorito_var.set(r[5] or 0); wishlist_var.set(r[6] or 0); backlog_var.set(r[7] or 0)
        data_ini_var.set(txt(r[8])); data_fim_var.set(txt(r[9])); horas_var.set(txt(r[10])); progresso_var.set(txt(r[11]))
        ano_var.set(txt(r[12])); genero_var.set(txt(r[13])); comentario_var.set(txt(r[14]))
        btn_salvar.config(text="Salvar alterações"); btn_cancelar.config(state="normal")
        feedback(f"Editando '{r[1]}'.", INFO); entry_nome.focus_set()
    def acao_remover():
        r = jogo_selecionado()
        if r is None: return
        if confirma(f"Remover o jogo '{r[1]}'?"):
            remover_jogo(r[0])
            if editando["id"] == r[0]: limpar_form()
            atualizar_listagem(); feedback(f"Jogo '{r[1]}' removido.")
    def duplo_clique(e):
        if tree.identify_row(e.y): acao_editar()
    tree.bind("<Double-1>", duplo_clique)
    btn_editar = tb.Button(rodape, text="Editar selecionado", bootstyle=INFO, command=acao_editar)
    btn_editar.pack(side="left"); tooltip(btn_editar, "Carrega o jogo no formulário (ou dê duplo clique na linha)")
    btn_remover = tb.Button(rodape, text="Remover selecionado", bootstyle=DANGER, command=acao_remover)
    btn_remover.pack(side="left", padx=6); tooltip(btn_remover, "Remove o jogo selecionado")
    voltar = tb.Button(rodape, text="Voltar ao menu", bootstyle=SECONDARY, command=menu_principal)
    voltar.pack(side="right")
    atualizar_listagem()

def iniciar():
    global root
    root = tb.Window(themename="cyborg")
    root.title("Biblioteca Gamer")
    root.geometry("1100x800")
    menu_principal()
    root.mainloop()
