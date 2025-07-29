"""
views/ui.py
Interface Tkinter usando ttkbootstrap — visual moderno, tooltips simples, barra de progresso.
CUIDADO: Requer ttkbootstrap e pillow!
"""

import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from controllers.controller import *

# ==== Auxiliares Visuais ====

def carregar_icone(nome_arquivo, tamanho=(20,20)):
    """Retorna PhotoImage do PNG na pasta /imagens (ou None se não encontrar)."""
    try:
        img = Image.open(f"imagens/{nome_arquivo}").resize(tamanho)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None

def tooltip(widget, text):
    """Tooltip (dica ao passar mouse no widget)."""
    tip = tk.Toplevel(widget)
    tip.withdraw(); tip.wm_overrideredirect(True)
    label = tk.Label(tip, text=text, background="#333", foreground="white", padx=6, pady=3)
    label.pack()
    def enter(e):
        x_root = widget.winfo_rootx() + 20
        y_root = widget.winfo_rooty() + 40
        tip.wm_geometry(f"+{x_root}+{y_root}")
        tip.deiconify()
    def leave(e): tip.withdraw()
    widget.bind("<Enter>", enter); widget.bind("<Leave>", leave)

# ==== Janela principal Tkinter (global root) ====
root = None

def limpar_frame():
    """Limpa tudo na janela root para abrir tela nova."""
    for w in root.winfo_children():
        w.destroy()

def barra_progresso(frm):
    """Mostra barra tipo 'meter' com % de jogos zerados."""
    todos = listar_jogos()
    total = len(todos)
    zerados = sum(1 for r in todos if r[3] and "zerad" in r[3].lower())
    # Exemplo: status = "Zerado"
    if total > 0:
        tb.Meter(frm, bootstyle=SUCCESS, subtext="Zerados",
            amountused=zerados, amounttotal=total,
            textfont="Arial 10 bold", stripethickness=7
        ).pack(pady=10)

def menu_principal():
    """Tela inicial de navegação/gamer e troca de tema."""
    limpar_frame()
    frm = tb.Frame(root)
    frm.pack(fill="both", expand=True)
    tk.Label(frm, text="🎮 Biblioteca Gamer", font=('Arial', 22, 'bold')).pack(pady=20)
    btn_console = tb.Button(frm, text="Consoles/Plataformas", width=25, bootstyle=PRIMARY, command=tela_consoles)
    btn_console.pack(pady=8)
    btn_jogo = tb.Button(frm, text="Jogos", width=25, bootstyle=SUCCESS, command=tela_jogos)
    btn_jogo.pack(pady=8)
    btn_sair = tb.Button(frm, text="Sair", width=25, bootstyle=DANGER, command=root.destroy)
    btn_sair.pack(pady=15)
    # Alternador de tema claro/escuro
    temas = ["darkly", "cyborg", "solar", "journal"]
    def alternar_tema():
        atual = root.style.theme.name
        idx = (temas.index(atual) + 1) % len(temas) if atual in temas else 0
        root.style.theme_use(temas[idx])
    tb.Button(frm, text="Alternar Tema", bootstyle=SECONDARY, command=alternar_tema).pack(pady=4)
    barra_progresso(frm) # Medidor: quantos jogos zerados

def tela_consoles():
    """Cadastro, listagem, remoção de consoles. Com ícone e tooltip."""
    limpar_frame()
    frm = tb.Frame(root)
    frm.pack(padx=15, pady=15)
    tb.Label(frm, text="Cadastro de Console/Plataforma", font=('Arial', 14, 'bold')).pack()
    nome_var = tk.StringVar()
    bx_nome = tb.Entry(frm, textvariable=nome_var, width=30)
    bx_nome.pack(pady=4)
    icone_add = carregar_icone("plus.png")
    def acao_cadastrar():
        nome = nome_var.get().strip()
        if cadastrar_console(nome):
            tb.Messagebox.ok(f"Console '{nome}' cadastrado!", title="Sucesso")
            nome_var.set("")
            atualizar_lista()
        else:
            tb.Messagebox.show_error("Nome inválido ou já cadastrado.", title="Erro")
    btn_add = tb.Button(frm, text="Cadastrar", bootstyle=SUCCESS, image=icone_add, compound=LEFT, command=acao_cadastrar)
    btn_add.pack()
    tooltip(btn_add, "Clique para cadastrar console")
    # ---- Listagem de consoles
    tree = tb.Treeview(frm, columns=("ID", "Nome"), show="headings", bootstyle=PRIMARY)
    tree.heading("ID", text="ID")
    tree.column("ID", minwidth=30, width=50)
    tree.heading("Nome", text="Nome")
    tree.column("Nome", minwidth=100, width=220)
    tree.pack(pady=10)
    def atualizar_lista():
        tree.delete(*tree.get_children())
        for id_console, nome in buscar_consoles():
            tree.insert("", "end", iid=id_console, values=(id_console, nome))
    def remover_sel():
        sel = tree.selection()
        if not sel:
            tb.Messagebox.show_warning("Selecione um console para remover.", title="Aviso")
            return
        idc = int(sel[0])
        confirm = tb.Messagebox.yesno("Remover esse console (e seus jogos)?", title="Confirmação")
        if confirm:
            remover_console(idc)
            atualizar_lista()
    btn_rem = tb.Button(frm, text="Remover Selecionado", bootstyle=DANGER, command=remover_sel)
    btn_rem.pack()
    tooltip(btn_rem, "Remove console e jogos ligados a ele")
    voltar = tb.Button(frm, text="Voltar ao menu", bootstyle=SECONDARY, command=menu_principal)
    voltar.pack(pady=10)
    atualizar_lista()

def tela_jogos():
    """Tela de cadastro, filtro/listagem, edição/remoção de jogos."""
    limpar_frame()
    frm = tb.Frame(root, padding=10)
    frm.pack(fill="both", expand=True)
    tb.Label(frm, text="Cadastro de Jogo", font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=10)
    nome_var = tk.StringVar()
    console_var = tk.StringVar()
    status_var = tk.StringVar(value="Jogado")
    avaliacao_var = tk.IntVar()
    comentario_var = tk.StringVar()
    favorito_var = tk.IntVar()
    ano_var = tk.IntVar()
    genero_var = tk.StringVar()
    tb.Label(frm, text="Nome*:", anchor="w").grid(row=1, column=0, sticky="w")
    tb.Entry(frm, textvariable=nome_var, width=25).grid(row=1, column=1)
    tb.Label(frm, text="Console*:", anchor="w").grid(row=2, column=0, sticky="w")
    consoles = buscar_consoles()
    nomes_consoles = [nome for _, nome in consoles]
    # >>> CORREÇÃO do OptionMenu: só cria se existe pelo menos um console!
    if nomes_consoles:
        console_var.set(nomes_consoles[0])
        opt = tb.OptionMenu(frm, console_var, *nomes_consoles)
        opt.grid(row=2, column=1)
        tooltip(opt, "Selecione a plataforma")
    else:
        tb.Label(frm, text="Cadastre um console primeiro!", bootstyle=WARNING).grid(row=2, column=1)
    tb.Label(frm, text="Status:", anchor="w").grid(row=3, column=0, sticky="w")
    tb.Entry(frm, textvariable=status_var).grid(row=3, column=1)
    tb.Label(frm, text="Avaliação (1-10):", anchor="w").grid(row=4, column=0, sticky="w")
    tb.Entry(frm, textvariable=avaliacao_var).grid(row=4, column=1)
    tb.Label(frm, text="Comentário:").grid(row=5, column=0, sticky="w")
    tb.Entry(frm, textvariable=comentario_var).grid(row=5, column=1)
    tb.Checkbutton(frm, text="Favorito ⭐", variable=favorito_var, bootstyle=WARNING).grid(row=6, column=1, sticky="w")
    tb.Label(frm, text="Ano de Lançamento:", anchor="w").grid(row=7, column=0, sticky="w")
    tb.Entry(frm, textvariable=ano_var).grid(row=7, column=1)
    tb.Label(frm, text="Gênero:", anchor="w").grid(row=8, column=0, sticky="w")
    tb.Entry(frm, textvariable=genero_var).grid(row=8, column=1)
    def acao_cadastrar():
        nome = nome_var.get().strip()
        if not nome:
            tb.Messagebox.show_error("Nome do jogo é obrigatório.", title="Erro")
            return
        if not nomes_consoles:
            tb.Messagebox.show_error("Cadastre pelo menos um console antes!", title="Erro")
            return
        id_console = next((cid for cid, nome_c in consoles if nome_c == console_var.get()), None)
        cadastrar_jogo(
            nome,
            id_console,
            status_var.get(),
            avaliacao_var.get() or None,
            comentario_var.get(),
            favorito_var.get(),
            ano_var.get() or None,
            genero_var.get()
        )
        tb.Messagebox.ok(f"'{nome}' cadastrado!", title="Sucesso")
        nome_var.set(""); avaliacao_var.set(0); comentario_var.set(""); favorito_var.set(0)
        ano_var.set(0); genero_var.set("")
        atualizar_jogos()
    btn_add = tb.Button(frm, text="Cadastrar", bootstyle=SUCCESS, command=acao_cadastrar)
    btn_add.grid(row=10, column=1, pady=5, sticky="e")
    tooltip(btn_add, "Cadastrar novo jogo")
    tb.Separator(frm, orient="horizontal").grid(row=11, column=0, columnspan=2, sticky="we", pady=10)
    tb.Label(frm, text="Meus Jogos", font=("Arial", 13, "bold")).grid(row=12, column=0, sticky="w", pady=10)
    filtro_fav_var = tk.IntVar()
    tb.Checkbutton(frm, text="Apenas favoritos", variable=filtro_fav_var, command=lambda: atualizar_jogos()).grid(row=12, column=1, sticky="e")
    tb.Label(frm, text="Pesquisar por nome:").grid(row=13, column=0, sticky="e")
    pesquisa_var = tk.StringVar()
    tb.Entry(frm, textvariable=pesquisa_var, width=14).grid(row=13, column=1, sticky="w")
    # ----- Treeview dos jogos
    cols = ("ID", "Nome", "Console", "Status", "Avaliação", "Favorito")
    tree = tb.Treeview(frm, columns=cols, show="headings", bootstyle=INFO)
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=90)
    tree.grid(row=14, column=0, columnspan=2, sticky="nsew")
    frm.rowconfigure(14, weight=1)
    frm.columnconfigure(1, weight=1)
    def atualizar_jogos():
        tree.delete(*tree.get_children())
        favoritos = filtro_fav_var.get()
        todos = listar_jogos(apenas_favoritos=bool(favoritos))
        texto_pesquisa = pesquisa_var.get().lower().strip()
        if texto_pesquisa:
            todos = [row for row in todos if texto_pesquisa in row[1].lower()]
        star = "⭐"
        for row in todos:
            id_j, nome, nome_con, status, aval, fav = row
            tree.insert("", "end", iid=id_j, values=(
                id_j, nome, nome_con or "-", status or "-", aval if aval else "",
                star if fav else ""
            ))
        barra_progresso(frm)
    def remover_jogo_sel():
        sel = tree.selection()
        if not sel:
            tb.Messagebox.show_warning("Selecione um jogo para remover.", title="Aviso")
            return
        iid = int(sel[0])
        confirm = tb.Messagebox.yesno("Deseja remover esse jogo?", title="Confirmação")
        if confirm:
            remover_jogo(iid)
            atualizar_jogos()
    btn_rem = tb.Button(frm, text="Remover Selecionado", bootstyle=DANGER, command=remover_jogo_sel)
    btn_rem.grid(row=15, column=1, sticky="e", pady=4)
    tooltip(btn_rem, "Remove o jogo selecionado")
    # EDITAR JOGO (ao dar duplo clique – popular formulário para edição)
    def editar_jogo(event):
        sel = tree.selection()
        if not sel:
            return
        iid = int(sel[0])
        for row in listar_jogos():
            if row[0] == iid:
                nome_var.set(row[1])
                if row[2]: console_var.set(row[2])
                status_var.set(row[3] or "")
                avaliacao_var.set(row[4] if row[4] else 0)
                favorito_var.set(row[5])
                break
        def confirmar_edicao():
            id_console = next((cid for cid, nome_c in consoles if nome_c == console_var.get()), None)
            atualizar_jogo(
                iid,
                nome_var.get(),
                id_console,
                status_var.get(),
                avaliacao_var.get(),
                comentario_var.get(),
                favorito_var.get(),
                ano_var.get(),
                genero_var.get()
            )
            tb.Messagebox.ok("Jogo atualizado.", title="Editado")
            atualizar_jogos()
        btn_editar = tb.Button(frm, text="Salvar Edição", bootstyle=INFO, command=confirmar_edicao)
        btn_editar.grid(row=10, column=0, pady=5, sticky="w")
    tree.bind("<Double-1>", editar_jogo)
    pesquisa_var.trace_add("write", lambda *args: atualizar_jogos())
    voltar = tb.Button(frm, text="Voltar ao menu", bootstyle=SECONDARY, command=menu_principal)
    voltar.grid(row=16, column=1, sticky="e", pady=13)
    atualizar_jogos()

def iniciar():
    """Inicia a interface com tema moderno, pronto para navegação."""
    global root
    root = tb.Window(themename="cyborg")  # "cyborg", "darkly", "solar" etc
    root.title("Biblioteca Gamer")
    root.geometry("850x670")
    menu_principal()
    root.mainloop()
