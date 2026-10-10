"""
Tela de jogos: lista com filtros, ordenação, painel da capa e as ações de importar/exportar.
"""

import csv
import threading
import tkinter as tk
from tkinter import filedialog

import ttkbootstrap as tb
from ttkbootstrap.constants import DANGER, INFO, OUTLINE, SECONDARY, SUCCESS
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.tooltip import ToolTip

from controllers import controller as ctl
from views import base
from views.formulario import dialogo_jogo
from views.importar_steam import dialogo_steam

capas_baixando, capas_sem_steam = set(), set()  # ids com download em andamento / que a Steam não tem
CAPA_LISTA = (170, 255)

# (campo, título, largura, alinhamento) das colunas da tabela de jogos
COLUNAS_JOGOS = [
    ("nome", "Nome", 190, "w"), ("console", "Plataforma", 100, "center"), ("status", "Status", 95, "center"),
    ("avaliacao", "Nota", 45, "center"), ("favorito", "Fav", 40, "center"), ("wishlist", "Wishlist", 58, "center"),
    ("backlog", "Backlog", 58, "center"), ("ano_lancamento", "Ano", 45, "center"), ("horas_jogadas", "Horas", 48, "center"),
]
ICONES_LISTA = {"favorito": "⭐", "wishlist": "❤️", "backlog": "🔖"}


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


def baixar_capa_em_segundo_plano(id_jogo, ao_terminar):
    """Busca na Steam a capa que falta, sem travar a tela; ao_terminar() roda se ela foi gravada."""
    if id_jogo in capas_baixando or id_jogo in capas_sem_steam:
        return
    capas_baixando.add(id_jogo)
    resultado = []
    def baixar():
        try:
            resultado.append(ctl.baixar_capa_da_steam(id_jogo))
        except Exception:  # sem internet, banco ocupado...: tenta de novo em outra hora
            pass
    tarefa = threading.Thread(target=baixar, daemon=True)
    tarefa.start()
    def conferir():
        if tarefa.is_alive():
            base.root.after(150, conferir); return
        capas_baixando.discard(id_jogo)
        if resultado and resultado[0]:
            ao_terminar()
        elif resultado:
            capas_sem_steam.add(id_jogo)
    base.root.after(150, conferir)


def tela_jogos(abrir_novo=False, mensagem=""):
    base.limpar_frame()
    frm = tb.Frame(base.root, padding=(20, 14)); frm.pack(fill="both", expand=True)
    consoles = ctl.buscar_consoles()
    ids_consoles = {c["nome"]: c["id"] for c in consoles}
    jogos_listados = {}  # id -> linha exibida na tabela
    ordem = {"campo": "nome", "decrescente": False}

    # --- título e contador
    topo = tb.Frame(frm); topo.pack(fill="x")
    tb.Label(topo, text="Jogos cadastrados", font=("Arial", 14, "bold")).pack(side="left")
    contador = tk.StringVar()
    tb.Label(topo, textvariable=contador, bootstyle=SECONDARY).pack(side="left", padx=12)

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

    # --- rodapé, mensagem, painel da capa e tabela (a tabela por último, para ocupar o espaço que sobrar)
    rodape = tb.Frame(frm); rodape.pack(side="bottom", fill="x", pady=(8, 0))
    msg = tk.StringVar(value=mensagem)
    label_feedback = tb.Label(frm, textvariable=msg, bootstyle=SUCCESS); label_feedback.pack(side="bottom", anchor="w", pady=(4, 0))
    def feedback(texto, estilo=SUCCESS):
        label_feedback.config(bootstyle=estilo); msg.set(texto)
    painel = tb.Frame(frm, width=CAPA_LISTA[0] + 20); painel.pack(side="right", fill="y", padx=(12, 0), pady=3)
    painel.pack_propagate(False)
    label_capa = tb.Label(painel, text="", anchor="center"); label_capa.pack(pady=(0, 8))
    detalhe_nome = tb.Label(painel, text="", font=("Arial", 10, "bold"), wraplength=CAPA_LISTA[0], justify="center")
    detalhe_nome.pack()
    detalhe_info = tb.Label(painel, text="", bootstyle=SECONDARY, wraplength=CAPA_LISTA[0], justify="center")
    detalhe_info.pack(pady=(4, 0))
    area_tabela = tb.Frame(frm); area_tabela.pack(fill="both", expand=True, pady=3)
    tree = tb.Treeview(area_tabela, columns=[c[0] for c in COLUNAS_JOGOS], show="headings", bootstyle=INFO, selectmode="browse")
    for campo, titulo, largura, alinhamento in COLUNAS_JOGOS:
        tree.column(campo, width=largura, anchor=alinhamento)
    rolagem = tb.Scrollbar(area_tabela, orient="vertical", command=tree.yview); tree.configure(yscrollcommand=rolagem.set)
    rolagem.pack(side="right", fill="y"); tree.pack(side="left", fill="both", expand=True)

    def atualizar_painel(*_):
        if not tree.winfo_exists(): return  # a tela mudou enquanto uma capa era baixada
        sel = tree.selection()
        jogo = jogos_listados.get(int(sel[0])) if sel else None
        if jogo is None:
            label_capa.config(image="", text=""); label_capa.image = None
            detalhe_nome.config(text=""); detalhe_info.config(text="Selecione um jogo para ver a capa.")
            return
        base.mostrar_capa(label_capa, ctl.caminho_capa(jogo["id"]) if ctl.tem_capa(jogo["id"]) else None, CAPA_LISTA)
        if label_capa.image is None and jogo["steam_appid"]:
            baixar_capa_em_segundo_plano(jogo["id"], atualizar_painel)
        partes = [jogo["genero"], f"{jogo['horas_jogadas']} h jogadas" if jogo["horas_jogadas"] else "",
                  jogo["comentario"], jogo["progresso"]]
        detalhe_nome.config(text=jogo["nome"])
        detalhe_info.config(text="\n".join(p for p in partes if p))

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
        atualizar_painel()

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
        chk.pack(side="left", padx=4); ToolTip(chk, f"Mostrar só {campo}")
    tb.Button(filtros, text="Limpar filtros", bootstyle=(SECONDARY, OUTLINE), command=limpar_filtros).pack(side="left", padx=(12, 0))
    busca_var.trace_add("write", atualizar_listagem)
    f_console.bind("<<ComboboxSelected>>", atualizar_listagem); f_status.bind("<<ComboboxSelected>>", atualizar_listagem)
    tree.bind("<<TreeviewSelect>>", atualizar_painel)

    def apos_salvar(mensagem):
        atualizar_listagem(); feedback(mensagem)

    def exige_plataforma():
        if not consoles:
            Messagebox.show_warning("Cadastre ao menos uma plataforma antes de adicionar jogos.", title="Aviso", parent=base.root)
        return bool(consoles)

    def acao_novo(evento=None):
        if exige_plataforma():
            dialogo_jogo(consoles, ao_salvar=apos_salvar)

    def acao_editar(evento=None):
        id_jogo = base.selecionado(tree, "Selecione um jogo na lista!")
        if id_jogo is not None:
            dialogo_jogo(consoles, jogos_listados[id_jogo], ao_salvar=apos_salvar)

    def acao_remover(evento=None):
        id_jogo = base.selecionado(tree, "Selecione um jogo na lista!")
        if id_jogo is None: return
        nome = jogos_listados[id_jogo]["nome"]
        if base.confirma(f"Remover o jogo '{nome}'?"):
            ctl.remover_jogo(id_jogo); atualizar_listagem(); feedback(f"Jogo '{nome}' removido.")

    def acao_exportar():
        caminho = filedialog.asksaveasfilename(parent=base.root, title="Exportar jogos", defaultextension=".csv",
            initialfile="biblioteca_gamer.csv", filetypes=[("CSV", "*.csv")])
        if not caminho: return
        try:
            total = ctl.exportar_csv(caminho)
        except OSError as erro:
            Messagebox.show_error(f"Não foi possível gravar o arquivo:\n{erro}", title="Erro", parent=base.root); return
        feedback(f"{total} jogos exportados para {caminho}")

    def acao_importar():
        caminho = filedialog.askopenfilename(parent=base.root, title="Importar jogos", filetypes=[("CSV", "*.csv")])
        if not caminho: return
        try:
            importados, duplicados, erros = ctl.importar_csv(caminho)
        except (OSError, UnicodeDecodeError, csv.Error, ctl.ErroValidacao) as erro:
            Messagebox.show_error(f"Não foi possível importar o arquivo:\n{erro}", title="Erro", parent=base.root); return
        resumo = f"{importados} jogos importados, {duplicados} já existiam."
        if erros:
            detalhes = "\n".join(erros[:10]) + (f"\n... e mais {len(erros) - 10}." if len(erros) > 10 else "")
            Messagebox.show_warning(f"{resumo}\n\n{len(erros)} linhas foram ignoradas:\n{detalhes}", title="Importação", parent=base.root)
        tela_jogos(mensagem=resumo)  # redesenha: a importação pode ter criado plataformas

    def acao_steam():
        if exige_plataforma():
            dialogo_steam(consoles, ao_concluir=lambda resumo: tela_jogos(mensagem=resumo))

    def duplo_clique(evento):
        if tree.identify_row(evento.y): acao_editar()
    tree.bind("<Double-1>", duplo_clique)
    tree.bind("<Return>", acao_editar)
    tree.bind("<Delete>", acao_remover)

    btn_novo = tb.Button(rodape, text="Novo jogo", bootstyle=SUCCESS, command=acao_novo)
    btn_novo.pack(side="left"); ToolTip(btn_novo, "Cadastrar um jogo (Ctrl+N)")
    btn_editar = tb.Button(rodape, text="Editar selecionado", bootstyle=INFO, command=acao_editar)
    btn_editar.pack(side="left", padx=6); ToolTip(btn_editar, "Abre o jogo para edição (Enter ou duplo clique na linha)")
    btn_remover = tb.Button(rodape, text="Remover selecionado", bootstyle=DANGER, command=acao_remover)
    btn_remover.pack(side="left"); ToolTip(btn_remover, "Remove o jogo selecionado (Delete)")
    tb.Button(rodape, text="Voltar ao menu", bootstyle=SECONDARY, command=lambda: base.ir_para("menu")).pack(side="right")
    btn_dados = tb.Menubutton(rodape, text="Importar / Exportar", bootstyle=(SECONDARY, OUTLINE))
    menu_dados = tk.Menu(btn_dados, tearoff=False)
    menu_dados.add_command(label="Importar biblioteca da Steam...", command=acao_steam)
    menu_dados.add_separator()
    menu_dados.add_command(label="Exportar CSV (backup / Excel)...", command=acao_exportar)
    menu_dados.add_command(label="Importar CSV...", command=acao_importar)
    btn_dados.config(menu=menu_dados); btn_dados.pack(side="right", padx=6)

    base.atalhos_tela.update(buscar=entry_busca.focus_set, novo=acao_novo)
    atualizar_listagem()
    if abrir_novo:
        acao_novo()
