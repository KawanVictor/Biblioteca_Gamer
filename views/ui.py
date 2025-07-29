"""
Interface gráfica com Tkinter (views/ui.py).
Reúne todas as telas, formulários e interações visuais do usuário.
Organizado e explicativo!
"""

import tkinter as tk
from tkinter import ttk, messagebox

# Importa funções via controller
from controllers.controller import *
# (assim você pode trocar ou validar depois via controller.py)

# Variável global da janela principal
root = None

def limpar_frame():
    """
    Limpa todos widgets da janela principal.
    """
    for w in root.winfo_children():
        w.destroy()

def menu_principal():
    """
    Tela inicial (menu de navegação).
    """
    limpar_frame()
    frm = tk.Frame(root)
    frm.pack(pady=40)
    tk.Label(frm, text="Biblioteca Gamer", font=('Arial', 20, 'bold')).pack(pady=16)
    tk.Button(frm, text="Consoles/Plataformas", width=25, command=tela_consoles).pack(pady=8)
    tk.Button(frm, text="Jogos", width=25, command=tela_jogos).pack(pady=8)
    tk.Button(frm, text="Sair", width=25, command=root.destroy).pack(pady=15)

def tela_consoles():
    """
    Cadastro, listagem e remoção de consoles/plataformas.
    """
    limpar_frame()
    frm = tk.Frame(root)
    frm.pack(padx=15, pady=15)

    tk.Label(frm, text="Cadastro de Console/Plataforma", font=('Arial', 14, 'bold')).pack()
    nome_var = tk.StringVar()
    bx_nome = tk.Entry(frm, textvariable=nome_var, width=30)
    bx_nome.pack(pady=4)
    def acao_cadastrar():
        nome = nome_var.get().strip()
        if cadastrar_console(nome):
            messagebox.showinfo("Sucesso", f"Console '{nome}' cadastrado!")
            nome_var.set("")
            atualizar_lista()
        else:
            messagebox.showerror("Erro", "Nome inválido ou já cadastrado.")
    tk.Button(frm, text="Cadastrar", command=acao_cadastrar).pack()

    tree = ttk.Treeview(frm, columns=("ID", "Nome"), show="headings")
    tree.heading("ID", text="ID")
    tree.column("ID", minwidth=30, width=50)
    tree.heading("Nome", text="Nome")
    tree.column("Nome", minwidth=100, width=220)
    tree.pack(pady=10)

    def atualizar_lista():
        for row in tree.get_children():
            tree.delete(row)
        for id_console, nome in buscar_consoles():
            tree.insert("", "end", iid=id_console, values=(id_console, nome))

    def remover_sel():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um console para remover.")
            return
        idc = int(sel[0])
        confirm = messagebox.askyesno("Confirmação",
            "Remover esse console irá remover também todos os jogos dessa plataforma. Prosseguir?")
        if confirm:
            remover_console(idc)
            atualizar_lista()

    tk.Button(frm, text="Remover Selecionado", fg="red", command=remover_sel).pack()
    tk.Button(frm, text="Voltar ao menu", command=menu_principal).pack(pady=10)
    atualizar_lista()

def tela_jogos():
    """
    Cadastro, listagem, filtro, edição e remoção de jogos.
    """
    limpar_frame()
    frm = tk.Frame(root)
    frm.pack(fill="both", expand=True, padx=20, pady=10)
    titulo = tk.Label(frm, text="Cadastro de Jogo", font=("Arial", 14, "bold"))
    titulo.grid(row=0, column=0, columnspan=2, sticky="w", pady=10)

    # Variáveis formulário
    nome_var = tk.StringVar()
    console_var = tk.StringVar()
    status_var = tk.StringVar(value="Jogado")
    avaliacao_var = tk.IntVar()
    comentario_var = tk.StringVar()
    favorito_var = tk.IntVar()
    ano_var = tk.IntVar()
    genero_var = tk.StringVar()

    # Campos do formulário alinhados com grid
    tk.Label(frm, text="Nome*:", anchor="w").grid(row=1, column=0, sticky="w")
    tk.Entry(frm, textvariable=nome_var, width=25).grid(row=1, column=1)
    tk.Label(frm, text="Console*:", anchor="w").grid(row=2, column=0, sticky="w")
    consoles = buscar_consoles()
    nomes_consoles = [nome for _, nome in consoles]
    if nomes_consoles:
        console_var.set(nomes_consoles[0])
    tk.OptionMenu(frm, console_var, *nomes_consoles).grid(row=2, column=1)
    tk.Label(frm, text="Status:", anchor="w").grid(row=3, column=0, sticky="w")
    tk.Entry(frm, textvariable=status_var).grid(row=3, column=1)
    tk.Label(frm, text="Avaliação (1-10):", anchor="w").grid(row=4, column=0, sticky="w")
    tk.Entry(frm, textvariable=avaliacao_var).grid(row=4, column=1)
    tk.Label(frm, text="Comentário:").grid(row=5, column=0, sticky="w")
    tk.Entry(frm, textvariable=comentario_var).grid(row=5, column=1)
    tk.Checkbutton(frm, text="Favorito", variable=favorito_var).grid(row=6, column=1, sticky="w")
    tk.Label(frm, text="Ano de Lançamento:", anchor="w").grid(row=7, column=0, sticky="w")
    tk.Entry(frm, textvariable=ano_var).grid(row=7, column=1)
    tk.Label(frm, text="Gênero:", anchor="w").grid(row=8, column=0, sticky="w")
    tk.Entry(frm, textvariable=genero_var).grid(row=8, column=1)

    def acao_cadastrar():
        """
        Coleta dados do formulário e chama cadastro no banco.
        """
        nome = nome_var.get().strip()
        if not nome:
            messagebox.showerror("Erro", "Nome do jogo é obrigatório.")
            return
        if not console_var.get():
            messagebox.showerror("Erro", "Escolha um console.")
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
        messagebox.showinfo("Sucesso", f"'{nome}' cadastrado!")
        nome_var.set(""); avaliacao_var.set(0); comentario_var.set(""); favorito_var.set(0)
        ano_var.set(0); genero_var.set("")
        atualizar_jogos()

    tk.Button(frm, text="Cadastrar", width=12, command=acao_cadastrar).grid(row=10, column=1, pady=5, sticky="e")

    # ---------- LISTAGEM ---------------
    sep = ttk.Separator(frm, orient="horizontal")
    sep.grid(row=11, column=0, columnspan=2, sticky="we", pady=10)

    tk.Label(frm, text="Meus Jogos", font=("Arial", 13, "bold")).grid(row=12, column=0, sticky="w", pady=10)
    
    filtro_fav_var = tk.IntVar()
    tk.Checkbutton(frm, text="Apenas favoritos", variable=filtro_fav_var, command=lambda: atualizar_jogos()).grid(row=12, column=1, sticky="e")
    tk.Label(frm, text="Pesquisar por nome:").grid(row=13, column=0, sticky="e")
    pesquisa_var = tk.StringVar()
    tk.Entry(frm, textvariable=pesquisa_var, width=14).grid(row=13, column=1, sticky="w")

    cols = ("ID", "Nome", "Console", "Status", "Avaliação", "Favorito")
    tree = ttk.Treeview(frm, columns=cols, show="headings", selectmode="browse")
    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, anchor="center", width=100)
    tree.grid(row=14, column=0, columnspan=2, sticky="nsew")
    frm.rowconfigure(14, weight=1)
    frm.columnconfigure(1, weight=1)

    def atualizar_jogos():
        """
        Atualiza tabela de jogos, com filtros de favorito e pesquisa.
        """
        tree.delete(*tree.get_children())
        favoritos = filtro_fav_var.get()
        todos = listar_jogos(apenas_favoritos=bool(favoritos))
        texto_pesquisa = pesquisa_var.get().lower().strip()
        if texto_pesquisa:
            todos = [row for row in todos if texto_pesquisa in row[1].lower()]
        for row in todos:
            id_j, nome, nome_con, status, aval, fav = row
            tree.insert("", "end", iid=id_j, values=(
                id_j, nome, nome_con or "-", status or "-", aval if aval else "", "Sim" if fav else "Não"
            ))

    def remover_jogo_sel():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione um jogo para remover.")
            return
        iid = int(sel[0])
        confirm = messagebox.askyesno("Confirmação", "Deseja remover esse jogo?")
        if confirm:
            remover_jogo(iid)
            atualizar_jogos()

    tk.Button(frm, text="Remover Selecionado", fg="red", command=remover_jogo_sel).grid(row=15, column=1, sticky="e", pady=4)

    # EDITAR JOGO — duplo clique
    def editar_jogo(event):
        sel = tree.selection()
        if not sel:
            return
        iid = int(sel[0])
        for row in listar_jogos():
            if row[0] == iid:
                nome_var.set(row[1])
                if row[2]:
                    console_var.set(row[2])
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
            messagebox.showinfo("Editado", "Jogo atualizado.")
            atualizar_jogos()
        tk.Button(frm, text="Salvar Edição", fg="blue", command=confirmar_edicao).grid(row=10, column=0, pady=5, sticky="w")
    
    tree.bind("<Double-1>", editar_jogo)
    pesquisa_var.trace("w", lambda *args: atualizar_jogos())

    tk.Button(frm, text="Voltar ao menu", command=menu_principal).grid(row=16, column=1, sticky="e", pady=13)
    atualizar_jogos()

def iniciar():
    """
    Inicia a interface principal.
    """
    global root
    root = tk.Tk()
    root.title("Biblioteca Gamer")
    root.geometry("800x650")
    menu_principal()
    root.mainloop()
