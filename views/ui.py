import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from controllers.controller import *

root = None

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
            tb.Messagebox.show_warning("Selecione uma plataforma!", title="Aviso"); return
        idc = int(sel[0])
        confirm = tb.Messagebox.yesno("Remover plataforma também apagará os jogos associados. Continuar?", title="Confirmar")
        if confirm:
            remover_console(idc); atualizar_lista(); msg.set("Plataforma removida.")
    btn_remover = tb.Button(frm, text="Remover selecionada", bootstyle=DANGER, command=remover_sel)
    btn_remover.pack(pady=(0,8)); tooltip(btn_remover, "Remove a plataforma e todos os jogos nela")
    voltar = tb.Button(frm, text="Voltar ao menu", bootstyle=SECONDARY, command=menu_principal)
    voltar.pack(); atualizar_lista()

def tela_jogos():
    limpar_frame()
    frm = tb.Frame(root); frm.pack(fill="both", expand=True, padx=25, pady=17)
    # Bloco dados básicos
    bloco_dados = tb.LabelFrame(frm, text="Dados do Jogo", bootstyle=INFO); bloco_dados.pack(fill="x", padx=8, pady=6)
    nome_var = tk.StringVar()
    tb.Label(bloco_dados, text="Nome*", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", pady=3)
    entry_nome = tb.Entry(bloco_dados, textvariable=nome_var, width=28, bootstyle=PRIMARY)
    entry_nome.grid(row=0, column=1, padx=6, pady=3)
    tb.Label(bloco_dados, text="Plataforma*", font=("Arial", 11, "bold")).grid(row=1, column=0, sticky="w")
    consoles = buscar_consoles(); nomes_consoles = [nome for _, nome in consoles]
    console_var = tk.StringVar()
    combo = tb.Combobox(bloco_dados, textvariable=console_var, values=nomes_consoles, font=("Arial", 10), bootstyle=PRIMARY, width=25)
    combo.grid(row=1, column=1, padx=6, pady=3); combo.set("Escolha a plataforma...")
    if not nomes_consoles: combo.config(state="disabled")
    tooltip(combo, "Selecione uma plataforma cadastrada")
    bloco_dados.columnconfigure(1, weight=1)
    # Bloco status/filtros
    bloco_status = tb.LabelFrame(frm, text="Status & Listas", bootstyle=PRIMARY); bloco_status.pack(fill="x", padx=8, pady=4)
    status_var = tk.StringVar(value="Jogado"); favorito_var = tk.IntVar(); wishlist_var = tk.IntVar(); backlog_var = tk.IntVar()
    tb.Label(bloco_status, text="Status:").grid(row=0, column=0, sticky="w")
    tb.Entry(bloco_status, textvariable=status_var, width=18).grid(row=0, column=1, padx=3, pady=2)
    tb.Checkbutton(bloco_status, text="Favorito ⭐", variable=favorito_var, bootstyle=WARNING).grid(row=1, column=0)
    tb.Checkbutton(bloco_status, text="Wishlist ❤️", variable=wishlist_var, bootstyle=INFO).grid(row=1, column=1)
    tb.Checkbutton(bloco_status, text="Backlog 🔖", variable=backlog_var, bootstyle=PRIMARY).grid(row=1, column=2)
    bloco_status.columnconfigure(1, weight=1)
    # Bloco extras
    tb.Separator(frm, orient="horizontal").pack(fill="x", padx=5, pady=5)
    bloco_extras = tb.LabelFrame(frm, text="Extras", bootstyle=SECONDARY); bloco_extras.pack(fill="x", padx=8, pady=2)
    avaliacao_var = tk.IntVar(); ano_var = tk.IntVar(); genero_var = tk.StringVar(); comentario_var = tk.StringVar()
    tb.Label(bloco_extras, text="Avaliação (1-10):").grid(row=0, column=0, sticky="w")
    tb.Entry(bloco_extras, textvariable=avaliacao_var, width=6).grid(row=0, column=1, padx=2)
    tb.Label(bloco_extras, text="Ano lançamento:").grid(row=1, column=0, sticky="w")
    tb.Entry(bloco_extras, textvariable=ano_var, width=8).grid(row=1, column=1, padx=2)
    tb.Label(bloco_extras, text="Gênero:").grid(row=2, column=0, sticky="w")
    tb.Entry(bloco_extras, textvariable=genero_var, width=18).grid(row=2, column=1, padx=2)
    tb.Label(bloco_extras, text="Comentário:").grid(row=3, column=0, sticky="w")
    tb.Entry(bloco_extras, textvariable=comentario_var, width=22).grid(row=3, column=1, padx=2)
    bloco_extras.columnconfigure(3, weight=1)
    # Bloco progresso
    tb.Separator(frm, orient="horizontal").pack(fill="x", padx=5, pady=3)
    bloco_progresso = tb.LabelFrame(frm, text="Progresso", bootstyle=SUCCESS); bloco_progresso.pack(fill="x", padx=8, pady=2)
    data_ini_var = tk.StringVar(); data_fim_var = tk.StringVar(); horas_var = tk.IntVar(); progresso_var = tk.StringVar()
    tb.Label(bloco_progresso, text="Data início (DD/MM/AAAA):").grid(row=0, column=0, sticky="w")
    tb.Entry(bloco_progresso, textvariable=data_ini_var, width=12).grid(row=0, column=1, padx=2)
    tb.Label(bloco_progresso, text="Data fim:").grid(row=1, column=0, sticky="w")
    tb.Entry(bloco_progresso, textvariable=data_fim_var, width=12).grid(row=1, column=1, padx=2)
    tb.Label(bloco_progresso, text="Horas jogadas:").grid(row=2, column=0, sticky="w")
    tb.Entry(bloco_progresso, textvariable=horas_var, width=6).grid(row=2, column=1, padx=2)
    tb.Label(bloco_progresso, text="Progresso/Notas:").grid(row=3, column=0, sticky="w")
    tb.Entry(bloco_progresso, textvariable=progresso_var, width=30).grid(row=3, column=1, padx=2)
    bloco_progresso.columnconfigure(1, weight=1)
    # feedback
    msg = tk.StringVar(value=""); label_feedback = tb.Label(frm, textvariable=msg, bootstyle=SUCCESS); label_feedback.pack(anchor="w", pady=(2,0))
    def acao_cadastrar():
        if not nome_var.get().strip():
            label_feedback.config(bootstyle=DANGER); msg.set("Preencha o nome do jogo."); return
        if not nomes_consoles or not console_var.get() or console_var.get() == "Escolha a plataforma...":
            label_feedback.config(bootstyle=DANGER); msg.set("Escolha uma plataforma cadastrada."); return
        id_console = next((cid for cid, nome_c in consoles if nome_c == console_var.get()), None)
        cadastrar_jogo(
            nome_var.get(), id_console, status_var.get(), avaliacao_var.get() or None, comentario_var.get(),
            favorito_var.get(), ano_var.get() or None, genero_var.get(),
            wishlist_var.get(), backlog_var.get(), data_ini_var.get(), data_fim_var.get(), horas_var.get() or None, progresso_var.get()
        )
        label_feedback.config(bootstyle=SUCCESS); msg.set(f"Jogo '{nome_var.get()}' cadastrado!")
        nome_var.set(""); console_var.set("Escolha a plataforma..."); status_var.set("Jogado"); avaliacao_var.set(0)
        comentario_var.set(""); favorito_var.set(0); ano_var.set(0); genero_var.set("")
        wishlist_var.set(0); backlog_var.set(0); data_ini_var.set(""); data_fim_var.set("")
        horas_var.set(0); progresso_var.set("")
        atualizar_listagem()
    btn_cadastrar = tb.Button(frm, text="Cadastrar jogo", bootstyle=SUCCESS, command=acao_cadastrar)
    btn_cadastrar.pack(anchor='e', pady=(8,4), padx=10)
    tooltip(btn_cadastrar, "Cadastrar novo jogo")
    # --- Listagem resumida com filtros (apenas para visual)
    sep = tb.Separator(frm, orient="horizontal"); sep.pack(fill="x", padx=5, pady=6)
    tb.Label(frm, text="Jogos cadastrados", font=("Arial", 12, "bold")).pack(anchor="w")
    cols = ("ID", "Nome", "Plataforma", "Status", "Fav", "Wishlist", "Backlog", "Ano")
    tree = tb.Treeview(frm, columns=cols, show="headings", bootstyle=INFO)
    for col in cols:
        tree.heading(col, text=col); tree.column(col, width=90, anchor="center")
    tree.pack(fill="x", padx=10, pady=3)
    def atualizar_listagem():
        tree.delete(*tree.get_children())
        for r in listar_jogos():
            tree.insert("", "end", iid=r[0], values=(
                r[0], r[1], r[2] or "-", r[3] or "-",
                "⭐" if r[5] else "", "❤️" if r[6] else "", "🔖" if r[7] else "", r[8] or ""
            ))
    atualizar_listagem()
    voltar = tb.Button(frm, text="Voltar ao menu", bootstyle=SECONDARY, command=menu_principal)
    voltar.pack(anchor='e', pady=(7,2), padx=9)

def iniciar():
    global root
    root = tb.Window(themename="cyborg")
    root.title("Biblioteca Gamer")
    root.geometry("1100x800")
    menu_principal()
    root.mainloop()
