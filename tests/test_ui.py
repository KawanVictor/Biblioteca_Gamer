"""Interface: abre as telas de verdade (janela oculta) e aciona botões, campos e atalhos."""

import os
import tkinter as tk
import unittest
from unittest import mock

import ttkbootstrap as tb

from controllers import controller as ctl
from tests import TesteComBanco
from views import ui


def descendentes(widget):
    for filho in widget.winfo_children():
        yield filho
        yield from descendentes(filho)


def da_classe(raiz, classe):
    return [w for w in descendentes(raiz) if w.winfo_class() == classe]


def botao(raiz, texto):
    return next(w for w in da_classe(raiz, "TButton") if w.cget("text") == texto)


def textos_variaveis(raiz):
    """Conteúdo dos rótulos ligados a uma variável (contador, mensagens de retorno), na ordem de criação."""
    return [w.getvar(str(w.cget("textvariable"))) for w in da_classe(raiz, "TLabel") if str(w.cget("textvariable"))]


def preencher(entry, texto):
    entry.delete(0, "end"); entry.insert(0, texto)


class TesteInterface(TesteComBanco):
    @classmethod
    def setUpClass(cls):
        try:
            ui.root = tb.Window(themename=ui.TEMA_PADRAO, size=(1000, 680))
        except tk.TclError as erro:
            raise unittest.SkipTest(f"sem ambiente gráfico: {erro}")
        ui.root.bind_all('<Control-n>', ui.atalho_global(ui.atalho_novo_jogo))

    @classmethod
    def tearDownClass(cls):
        ui.root.destroy()

    def setUp(self):
        super().setUp()
        self.root = ui.root
        self.avisos, self.perguntas, self.resposta = [], [], True
        def confirma(mensagem):
            self.perguntas.append(mensagem); return self.resposta
        for alvo, nome, substituto in (
            (ui.Messagebox, "show_warning", lambda m, **k: self.avisos.append(m)),
            (ui.Messagebox, "show_error", lambda m, **k: self.avisos.append(m)),
            (ui, "confirma", confirma),
        ):
            remendo = mock.patch.object(alvo, nome, substituto)
            remendo.start(); self.addCleanup(remendo.stop)
        self.pc = ctl.salvar_console("PC")
        self.ps5 = ctl.salvar_console("PS5")

    def tearDown(self):
        ui.limpar_frame()
        super().tearDown()

    # ---- apoio
    def tecla(self, widget, sequencia):
        """Tecla só chega ao widget que tem o foco do teclado."""
        widget.focus_force(); self.root.update()
        widget.event_generate(sequencia); self.root.update()

    def tabela(self):
        return da_classe(self.root, "Treeview")[0]

    def linhas(self):
        return [self.tabela().item(i, "values") for i in self.tabela().get_children()]

    def nomes(self):
        return [linha[0] for linha in self.linhas()]

    def selecionar(self, nome):
        arvore = self.tabela()
        arvore.selection_set(next(i for i in arvore.get_children() if arvore.item(i, "values")[0] == nome))

    def dialogo(self):
        abertos = [w for w in self.root.winfo_children() if w.winfo_class() == "Toplevel"]
        return abertos[0] if abertos else None

    def campos_dialogo(self):
        """(entradas, comboboxes) do formulário: nome, nota, ano, gênero, comentário, início, fim, horas, progresso."""
        return da_classe(self.dialogo(), "TEntry"), da_classe(self.dialogo(), "TCombobox")

    def tres_jogos(self):
        ctl.salvar_jogo({"nome": "Hades", "id_console": self.pc, "status": "Zerado", "favorito": 1, "avaliacao": "9", "ano_lancamento": "2020"})
        ctl.salvar_jogo({"nome": "Celeste", "id_console": self.pc, "backlog": 1, "data_inicio": "01/02/2024"})
        ctl.salvar_jogo({"nome": "Astro Bot", "id_console": self.ps5, "wishlist": 1, "avaliacao": "10"})

    # ---- consoles
    def test_consoles_cadastrar_renomear_e_remover(self):
        ctl.salvar_jogo({"nome": "A", "id_console": self.pc}); ctl.salvar_jogo({"nome": "B", "id_console": self.pc})
        ui.tela_consoles()
        entrada = da_classe(self.root, "TEntry")[0]
        self.assertEqual(self.linhas(), [("PC", "2"), ("PS5", "0")])

        botao(self.root, "Remover selecionada").invoke()
        self.assertEqual(self.avisos, ["Selecione uma plataforma!"])

        preencher(entrada, "Switch"); self.tecla(entrada, "<Return>")
        self.assertEqual(self.nomes(), ["PC", "PS5", "Switch"])
        preencher(entrada, "switch"); botao(self.root, "Cadastrar").invoke()
        self.assertIn("já existe", textos_variaveis(self.root)[0])

        self.selecionar("Switch")
        with mock.patch.object(ui.Querybox, "get_string", lambda *a, **k: "Nintendo Switch"):
            botao(self.root, "Renomear selecionada").invoke()
        self.assertEqual(self.nomes(), ["Nintendo Switch", "PC", "PS5"])

        self.selecionar("PC"); self.resposta = False
        botao(self.root, "Remover selecionada").invoke()
        self.assertIn("Os 2 jogos", self.perguntas[-1])
        self.assertEqual(len(self.linhas()), 3)  # respondeu "Não": nada foi apagado
        self.resposta = True
        botao(self.root, "Remover selecionada").invoke()
        self.assertEqual(self.nomes(), ["Nintendo Switch", "PS5"])
        self.assertEqual(ctl.contar_jogos(), 0)

    # ---- jogos
    def test_novo_jogo_sem_plataforma_cadastrada_avisa(self):
        ctl.remover_console(self.pc); ctl.remover_console(self.ps5)
        ui.tela_jogos()
        botao(self.root, "Novo jogo").invoke()
        self.assertIsNone(self.dialogo())
        self.assertIn("Cadastre ao menos uma plataforma", self.avisos[0])

    def test_cadastrar_pelo_dialogo(self):
        ui.tela_jogos()
        botao(self.root, "Novo jogo").invoke()
        entradas, combos = self.campos_dialogo()
        self.assertEqual(len(entradas), 9)
        self.assertEqual([str(c.cget("state")) for c in combos], ["readonly", "readonly"])
        self.assertEqual(list(combos[1].cget("values")), ctl.STATUS_JOGO)
        self.assertEqual((entradas[5].get(), entradas[6].get()), ("", ""))  # datas começam vazias

        preencher(entradas[0], "Hades")
        botao(self.dialogo(), "Cadastrar jogo").invoke()
        self.assertEqual(textos_variaveis(self.dialogo()), ["Escolha uma plataforma cadastrada."])
        combos[0].set("PC"); preencher(entradas[1], "abc")
        botao(self.dialogo(), "Cadastrar jogo").invoke()
        self.assertEqual(textos_variaveis(self.dialogo()), ["Avaliação deve ser um número inteiro."])
        self.assertEqual(self.linhas(), [])  # nada gravado enquanto houver erro

        preencher(entradas[1], ""); preencher(entradas[2], "2020"); preencher(entradas[5], "05/03/2024")
        combos[1].set("Zerado")
        self.tecla(self.dialogo(), "<Return>")
        self.assertIsNone(self.dialogo())
        self.assertEqual(self.linhas(), [("Hades", "PC", "Zerado", "", "", "", "", "2020", "")])
        self.assertEqual(textos_variaveis(self.root), ["1 jogos", "Jogo 'Hades' cadastrado!"])
        self.assertEqual(ctl.listar_jogos()[0]["data_inicio"], "2024-03-05")

    def test_editar_carrega_e_grava_todos_os_campos(self):
        ctl.salvar_jogo({"nome": "Zelda", "id_console": self.ps5, "status": "Pausado", "avaliacao": "9", "favorito": 1,
            "ano_lancamento": "2023", "genero": "Aventura", "comentario": "bom", "data_inicio": "01/06/2023",
            "data_fim": "30/06/2023", "horas_jogadas": "80", "progresso": "metade"})
        ui.tela_jogos()
        botao(self.root, "Editar selecionado").invoke()
        self.assertEqual(self.avisos, ["Selecione um jogo na lista!"])

        self.selecionar("Zelda")
        self.tecla(self.tabela(), "<Return>")
        entradas, combos = self.campos_dialogo()
        self.assertEqual([e.get() for e in entradas], ["Zelda", "9", "2023", "Aventura", "bom", "01/06/2023", "30/06/2023", "80", "metade"])
        self.assertEqual([c.get() for c in combos], ["PS5", "Pausado"])

        preencher(entradas[0], "Zelda TOTK"); preencher(entradas[7], "120"); combos[0].set("PC"); combos[1].set("Zerado")
        botao(self.dialogo(), "Salvar alterações").invoke()
        self.assertEqual(self.linhas(), [("Zelda TOTK", "PC", "Zerado", "9", "⭐", "", "", "2023", "120")])
        self.assertEqual(textos_variaveis(self.root)[1], "Jogo 'Zelda TOTK' atualizado!")

        self.selecionar("Zelda TOTK")
        botao(self.root, "Editar selecionado").invoke()
        botao(self.dialogo(), "Cancelar").invoke()
        self.assertIsNone(self.dialogo())
        self.assertEqual(self.nomes(), ["Zelda TOTK"])

    def test_remover(self):
        self.tres_jogos()
        ui.tela_jogos()
        self.selecionar("Celeste"); self.resposta = False
        self.tecla(self.tabela(), "<Delete>")
        self.assertEqual(self.perguntas, ["Remover o jogo 'Celeste'?"])
        self.assertEqual(len(self.linhas()), 3)
        self.resposta = True
        botao(self.root, "Remover selecionado").invoke()
        self.assertEqual(self.nomes(), ["Astro Bot", "Hades"])

    def test_filtros_contador_e_limpar(self):
        self.tres_jogos()
        ui.tela_jogos()
        busca = da_classe(self.root, "TEntry")[0]
        f_console, f_status = da_classe(self.root, "TCombobox")
        fav, wish, back = da_classe(self.root, "TCheckbutton")
        contador = lambda: textos_variaveis(self.root)[0]
        self.assertEqual((self.nomes(), contador()), (["Astro Bot", "Celeste", "Hades"], "3 jogos"))

        preencher(busca, "ele")
        self.assertEqual((self.nomes(), contador()), (["Celeste"], "1 de 3 jogos"))
        preencher(busca, "")
        f_console.set("PC"); f_console.event_generate("<<ComboboxSelected>>"); self.root.update()
        self.assertEqual(self.nomes(), ["Celeste", "Hades"])
        f_status.set("Zerado"); f_status.event_generate("<<ComboboxSelected>>"); self.root.update()
        self.assertEqual(self.nomes(), ["Hades"])
        back.invoke()
        self.assertEqual(self.nomes(), [])
        botao(self.root, "Limpar filtros").invoke()
        self.assertEqual((self.nomes(), contador(), f_console.get(), f_status.get()), (["Astro Bot", "Celeste", "Hades"], "3 jogos", "Todas", "Todos"))
        wish.invoke(); self.assertEqual(self.nomes(), ["Astro Bot"]); wish.invoke()
        fav.invoke(); self.assertEqual(self.nomes(), ["Hades"])

    def test_ordenar_pelo_cabecalho(self):
        self.tres_jogos()
        ui.tela_jogos()
        clicar = lambda campo: self.root.tk.call(self.tabela().heading(campo, "command"))
        self.assertEqual(self.tabela().heading("nome", "text"), "Nome ▲")
        clicar("nome")
        self.assertEqual((self.nomes(), self.tabela().heading("nome", "text")), (["Hades", "Celeste", "Astro Bot"], "Nome ▼"))
        clicar("avaliacao")  # Celeste não tem nota: fica no fim nas duas direções
        self.assertEqual(self.nomes(), ["Hades", "Astro Bot", "Celeste"])
        clicar("avaliacao")
        self.assertEqual((self.nomes(), self.tabela().heading("avaliacao", "text")), (["Astro Bot", "Hades", "Celeste"], "Nota ▼"))
        self.assertEqual(self.tabela().heading("nome", "text"), "Nome")

    def test_status_antigo_fora_da_lista_aparece_no_filtro(self):
        from database import db
        with db.conecta() as conn:
            conn.execute("INSERT INTO jogos (nome, id_console, status) VALUES ('Velho', ?, 'Jogado')", (self.pc,))
        ui.tela_jogos()
        f_status = da_classe(self.root, "TCombobox")[1]
        self.assertEqual(list(f_status.cget("values")), ["Todos"] + ctl.STATUS_JOGO + ["Jogado"])
        f_status.set("Jogado"); f_status.event_generate("<<ComboboxSelected>>"); self.root.update()
        self.assertEqual(self.nomes(), ["Velho"])

    def test_exportar_e_importar_pelos_botoes(self):
        self.tres_jogos()
        caminho = os.path.join(self.pasta, "saida.csv")
        ui.tela_jogos()
        with mock.patch.object(ui.filedialog, "asksaveasfilename", lambda **k: caminho):
            botao(self.root, "Exportar CSV").invoke()
        self.assertIn("3 jogos exportados", textos_variaveis(self.root)[1])

        ctl.remover_console(self.ps5)  # leva o Astro Bot junto
        with mock.patch.object(ui.filedialog, "askopenfilename", lambda **k: caminho):
            botao(self.root, "Importar CSV").invoke()
        self.assertEqual(self.nomes(), ["Astro Bot", "Celeste", "Hades"])
        self.assertEqual(textos_variaveis(self.root)[1], "1 jogos importados, 2 já existiam.")
        self.assertIn("PS5", da_classe(self.root, "TCombobox")[0].cget("values"))  # plataforma recriada

        with mock.patch.object(ui.filedialog, "askopenfilename", lambda **k: ""):
            botao(self.root, "Importar CSV").invoke()  # cancelou a escolha do arquivo: nada acontece
        self.assertEqual(self.avisos, [])

    # ---- menu e janela
    def test_atalho_ctrl_n_abre_o_formulario_e_fica_inativo_com_dialogo_aberto(self):
        ui.menu_principal()
        self.root.deiconify(); self.root.update(); self.root.focus_force(); self.root.update()
        self.root.event_generate("<Control-n>"); self.root.update()
        primeiro = self.dialogo()
        self.assertIsNotNone(primeiro)
        self.assertEqual(len(da_classe(self.root, "Treeview")), 1)  # foi para a tela de jogos
        primeiro.event_generate("<Control-n>"); self.root.update()
        self.assertEqual(len([w for w in self.root.winfo_children() if w.winfo_class() == "Toplevel"]), 1)
        primeiro.event_generate("<Escape>"); self.root.update()
        self.assertIsNone(self.dialogo())

    def test_menu_progresso_sem_wishlist_tema_lembrado_e_ranking(self):
        ui.menu_principal()
        self.assertEqual([w for w in descendentes(self.root) if isinstance(w, tb.Meter)], [])  # sem jogos, sem barra
        botao(self.root, "Ver Ranking Favoritos").invoke()
        self.assertIn("Nenhum favorito ainda", " ".join(w.cget("text") for w in da_classe(self.dialogo(), "TLabel")))

        self.tres_jogos()
        ctl.salvar_jogo({"nome": "Sem nota", "id_console": self.pc, "favorito": 1})
        ui.menu_principal()
        medidor = next(w for w in descendentes(self.root) if isinstance(w, tb.Meter))
        self.assertEqual((medidor.amountusedvar.get(), medidor.amounttotalvar.get()), (1, 3))  # Astro Bot é wishlist
        botao(self.root, "Ver Ranking Favoritos").invoke()
        linhas = [w.cget("text") for w in da_classe(self.dialogo(), "TLabel")]
        self.assertEqual(linhas[1:], ["1. Hades (PC) — Nota: 9", "2. Sem nota (PC) — sem nota"])

        botao(self.root, "Alternar Tema").invoke()
        self.assertEqual(ctl.ler_config("tema"), "solar")
        self.assertEqual(self.root.style.theme.name, "solar")
        self.root.style.theme_use(ui.TEMA_PADRAO)

    def test_telas_cabem_no_tamanho_minimo_da_janela(self):
        self.tres_jogos()
        ui.tela_jogos(); self.root.update_idletasks()
        tela = self.root.winfo_children()[0]
        self.assertLessEqual(tela.winfo_reqwidth(), 900)
        # a tabela pede 10 linhas por padrão mas encolhe; o resto da tela precisa caber em 560
        self.assertLessEqual(tela.winfo_reqheight() - self.tabela().winfo_reqheight() + 120, 560)
        botao(self.root, "Novo jogo").invoke(); self.root.update_idletasks()
        self.assertLessEqual(self.dialogo().winfo_reqwidth(), 900)
        self.assertLessEqual(self.dialogo().winfo_reqheight(), 560)
        ui.menu_principal(); self.root.update_idletasks()
        self.assertLessEqual(self.root.winfo_children()[0].winfo_reqheight(), 560)


if __name__ == "__main__":
    unittest.main()
