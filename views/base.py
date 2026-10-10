"""
Base da interface: a janela principal, a troca de telas e as funções usadas por mais de uma tela.
"""

import io
import os
import sys

from PIL import Image, ImageTk
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.localization import MessageCatalog

root = None        # janela principal, criada em ui.iniciar()
telas = {}         # nome -> função que desenha a tela; preenchido em ui.py
atalhos_tela = {}  # atalhos que só valem na tela atual, ex.: {"buscar": função}

TEMAS = ["darkly", "cyborg", "solar", "journal"]
TEMA_PADRAO = "cyborg"


def ir_para(nome, **opcoes):
    """Troca a tela mostrada na janela. As telas se chamam pelo nome para não precisarem importar umas às outras."""
    telas[nome](**opcoes)


def recurso(caminho):
    """Arquivo que acompanha o programa (no .exe, os recursos ficam em uma pasta temporária)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, caminho)


def confirma(mensagem):
    # yesno devolve o texto (traduzido) do botão clicado, não um booleano
    return Messagebox.yesno(mensagem, title="Confirmar", parent=root) == MessageCatalog.translate("Yes")


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


def foto_capa(imagem, tamanho):
    """PhotoImage reduzida para caber em tamanho, a partir de um caminho ou de bytes. None se não for imagem."""
    try:
        with Image.open(io.BytesIO(imagem) if isinstance(imagem, bytes) else imagem) as img:
            img = img.convert("RGB")
            img.thumbnail(tamanho)
            return ImageTk.PhotoImage(img)
    except (OSError, ValueError):
        return None


def mostrar_capa(label, imagem, tamanho):
    """Põe a capa no label (ou o texto 'Sem capa'). Devolve True se havia imagem para mostrar."""
    foto = foto_capa(imagem, tamanho) if imagem else None
    label.config(image=foto or "", text="" if foto else "Sem capa")
    label.image = foto  # o Tk não guarda a referência: sem isto a imagem some
    return foto is not None


def com_espera(janela, funcao):
    """Roda uma consulta demorada (internet) mostrando o cursor de espera."""
    janela.config(cursor="watch"); janela.update_idletasks()
    try:
        return funcao()
    finally:
        janela.config(cursor="")
