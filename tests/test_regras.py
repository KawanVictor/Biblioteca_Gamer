"""Banco e controlador: migração, validações, filtros e CSV."""

import os
import sqlite3
import unittest

from controllers import controller as ctl
from database import db
from tests import TesteComBanco


def jogo(nome="Hades", id_console=1, **extras):
    return {"nome": nome, "id_console": id_console, **extras}


class TesteCaminhoDoBanco(unittest.TestCase):
    def test_banco_fica_ao_lado_do_projeto_e_nao_na_pasta_atual(self):
        raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertEqual(db.CAMINHO_DB, os.path.join(raiz, "biblioteca_gamer.db"))


class TesteMigracao(TesteComBanco):
    def setUp(self):
        super().setUp()
        os.remove(db.CAMINHO_DB)

    def _banco_antigo(self):
        """Banco como a versão anterior do app criava: status livre, datas DD/MM/AAAA, sem versão."""
        conn = sqlite3.connect(db.CAMINHO_DB)
        conn.executescript("""
            CREATE TABLE consoles (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE NOT NULL);
            CREATE TABLE jogos (
                id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT NOT NULL, id_console INTEGER, status TEXT,
                avaliacao INTEGER, comentario TEXT, favorito INTEGER DEFAULT 0, ano_lancamento INTEGER, genero TEXT
            );
            INSERT INTO consoles (nome) VALUES ('PC');
            INSERT INTO jogos (nome, id_console, status) VALUES
                ('A', 1, 'zerado'), ('B', 1, 'Zerado 100%'), ('C', 1, 'Jogado'), ('D', 1, 'JOGANDO'), ('E', 1, NULL);
        """)
        conn.commit(); conn.close()

    def test_banco_antigo_ganha_colunas_e_status_da_lista(self):
        self._banco_antigo()
        db.cria_tabelas()
        status = {j["nome"]: j["status"] for j in db.listar_jogos()}
        self.assertEqual(status, {"A": "Zerado", "B": "Zerado", "C": "Jogado", "D": "Jogando", "E": None})
        self.assertEqual(db.listar_jogos()[0]["wishlist"], 0)  # coluna que não existia
        self.assertTrue(os.path.exists(os.path.join(self.pasta, "teste.backup-v0.db")))

    def test_datas_antigas_viram_iso_e_as_ilegiveis_ficam_como_estao(self):
        self._banco_antigo()
        conn = sqlite3.connect(db.CAMINHO_DB)
        conn.executescript("""
            ALTER TABLE jogos ADD COLUMN data_inicio TEXT; ALTER TABLE jogos ADD COLUMN data_fim TEXT;
            UPDATE jogos SET data_inicio = '05/03/2024', data_fim = 'mês passado' WHERE nome = 'A';
        """)
        conn.commit(); conn.close()
        db.cria_tabelas()
        a = db.listar_jogos(busca_nome="A")[0]
        self.assertEqual((a["data_inicio"], a["data_fim"]), ("2024-03-05", "mês passado"))

    def test_migracao_roda_uma_vez_so(self):
        db.cria_tabelas()
        ctl.salvar_console("PC")
        db.cria_tabelas()
        self.assertEqual(len(db.buscar_consoles()), 1)
        self.assertFalse(os.path.exists(os.path.join(self.pasta, "teste.backup-v1.db")))


class TesteConsoles(TesteComBanco):
    def test_nome_vazio_e_repetido_sao_recusados(self):
        ctl.salvar_console("PC")
        for nome in ("", "   ", "PC", "pc "):
            with self.assertRaises(ctl.ErroValidacao):
                ctl.salvar_console(nome)

    def test_renomear(self):
        pc = ctl.salvar_console("PC"); ctl.salvar_console("PS5")
        ctl.salvar_console("Computador", pc)
        self.assertEqual([c["nome"] for c in ctl.buscar_consoles()], ["Computador", "PS5"])
        ctl.salvar_console("computador", pc)  # mudar só a caixa do próprio nome é permitido
        with self.assertRaises(ctl.ErroValidacao):
            ctl.salvar_console("PS5", pc)

    def test_lista_traz_quantidade_de_jogos_e_remover_apaga_os_jogos(self):
        pc = ctl.salvar_console("PC"); ps5 = ctl.salvar_console("PS5")
        ctl.salvar_jogo(jogo("A", pc)); ctl.salvar_jogo(jogo("B", pc)); ctl.salvar_jogo(jogo("C", ps5))
        self.assertEqual({c["nome"]: c["total_jogos"] for c in ctl.buscar_consoles()}, {"PC": 2, "PS5": 1})
        ctl.remover_console(pc)
        self.assertEqual([j["nome"] for j in ctl.listar_jogos()], ["C"])


class TesteJogos(TesteComBanco):
    def setUp(self):
        super().setUp()
        self.pc = ctl.salvar_console("PC")
        self.ps5 = ctl.salvar_console("PS5")

    def assertRecusa(self, trecho, **campos):
        with self.assertRaises(ctl.ErroValidacao) as contexto:
            ctl.salvar_jogo(jogo(**campos))
        self.assertIn(trecho, str(contexto.exception))

    def test_campos_opcionais_vazios_viram_nulo(self):
        ctl.salvar_jogo(jogo(avaliacao="", ano_lancamento="  ", horas_jogadas="", data_inicio=""))
        j = ctl.listar_jogos()[0]
        self.assertEqual((j["avaliacao"], j["ano_lancamento"], j["horas_jogadas"], j["data_inicio"]), (None, None, None, None))
        self.assertEqual((j["status"], j["console"], j["favorito"]), ("Jogando", "PC", 0))

    def test_validacoes(self):
        self.assertRecusa("nome", nome="  ")
        self.assertRecusa("plataforma", id_console=None)
        self.assertRecusa("número inteiro", avaliacao="abc")
        self.assertRecusa("maior que 10", avaliacao="11")
        self.assertRecusa("menor que 1", avaliacao="0")
        self.assertRecusa("menor que 0", horas_jogadas="-3")
        self.assertRecusa("Ano de lançamento", ano_lancamento="20")
        self.assertRecusa("DD/MM/AAAA", data_inicio="31/02/2024")
        self.assertRecusa("anterior", data_inicio="10/01/2024", data_fim="09/01/2024")
        self.assertEqual(ctl.listar_jogos(), [])

    def test_datas_sao_gravadas_em_iso(self):
        ctl.salvar_jogo(jogo(data_inicio="05/03/2024", data_fim="2024-03-20"))
        j = ctl.listar_jogos()[0]
        self.assertEqual((j["data_inicio"], j["data_fim"]), ("2024-03-05", "2024-03-20"))
        self.assertEqual(ctl.data_para_br(j["data_inicio"]), "05/03/2024")

    def test_duplicado_so_na_mesma_plataforma(self):
        id_jogo = ctl.salvar_jogo(jogo("Hades", self.pc))
        with self.assertRaises(ctl.JogoDuplicado):
            ctl.salvar_jogo(jogo(" hades ", self.pc))
        ctl.salvar_jogo(jogo("Hades", self.ps5))
        ctl.salvar_jogo(jogo("Hades", self.pc, avaliacao="9"), id_jogo)  # editar o próprio jogo não é duplicata
        with self.assertRaises(ctl.JogoDuplicado):
            ctl.salvar_jogo(jogo("Hades", self.ps5), id_jogo)
        self.assertEqual(ctl.contar_jogos(), 2)

    def test_editar_altera_todos_os_campos(self):
        id_jogo = ctl.salvar_jogo(jogo("Zelda", self.pc))
        ctl.salvar_jogo(jogo("Zelda TOTK", self.ps5, status="Zerado", avaliacao="10", favorito=1, wishlist=1, backlog=1,
            ano_lancamento="2023", genero="Aventura", comentario="ótimo", data_inicio="01/06/2023",
            data_fim="30/06/2023", horas_jogadas="120", progresso="100%"), id_jogo)
        j = dict(ctl.listar_jogos()[0])
        self.assertEqual(j, {
            "id": id_jogo, "nome": "Zelda TOTK", "id_console": self.ps5, "status": "Zerado", "avaliacao": 10,
            "comentario": "ótimo", "favorito": 1, "ano_lancamento": 2023, "genero": "Aventura", "wishlist": 1,
            "backlog": 1, "data_inicio": "2023-06-01", "data_fim": "2023-06-30", "horas_jogadas": 120,
            "progresso": "100%", "console": "PS5",
        })

    def test_filtros(self):
        ctl.salvar_jogo(jogo("Hades", self.pc, status="Zerado", favorito=1))
        ctl.salvar_jogo(jogo("Hollow Knight", self.pc, backlog=1))
        ctl.salvar_jogo(jogo("Astro Bot", self.ps5, wishlist=1))
        nomes = lambda **f: [j["nome"] for j in ctl.listar_jogos(**f)]
        self.assertEqual(nomes(), ["Astro Bot", "Hades", "Hollow Knight"])
        self.assertEqual(nomes(busca_nome="h"), ["Hades", "Hollow Knight"])
        self.assertEqual(nomes(filtro_console=self.ps5), ["Astro Bot"])
        self.assertEqual(nomes(filtro_status="Zerado"), ["Hades"])
        self.assertEqual(nomes(apenas_favoritos=True), ["Hades"])
        self.assertEqual(nomes(apenas_wishlist=True), ["Astro Bot"])
        self.assertEqual(nomes(apenas_backlog=True, filtro_console=self.pc), ["Hollow Knight"])

    def test_progresso_ignora_a_wishlist(self):
        ctl.salvar_jogo(jogo("A", status="Zerado")); ctl.salvar_jogo(jogo("B"))
        ctl.salvar_jogo(jogo("C", wishlist=1)); ctl.salvar_jogo(jogo("D", wishlist=1, status="Zerado"))
        self.assertEqual(ctl.resumo_progresso(), (1, 2))

    def test_ranking_poe_os_sem_nota_no_fim(self):
        ctl.salvar_jogo(jogo("Sem nota", favorito=1)); ctl.salvar_jogo(jogo("Sete", favorito=1, avaliacao="7"))
        ctl.salvar_jogo(jogo("Dez", favorito=1, avaliacao="10")); ctl.salvar_jogo(jogo("Fora", avaliacao="10"))
        self.assertEqual([j["nome"] for j in ctl.ranking_favoritos()], ["Dez", "Sete", "Sem nota"])

    def test_config(self):
        self.assertEqual(ctl.ler_config("tema", "cyborg"), "cyborg")
        ctl.gravar_config("tema", "solar"); ctl.gravar_config("tema", "journal")
        self.assertEqual(ctl.ler_config("tema"), "journal")


class TesteCsv(TesteComBanco):
    def test_exportar_e_importar_em_outro_banco_preserva_tudo(self):
        pc = ctl.salvar_console("PC"); ps5 = ctl.salvar_console("PS5")
        ctl.salvar_jogo(jogo("Zelda; o \"jogo\"", ps5, status="Zerado", avaliacao="10", favorito=1, backlog=1,
            ano_lancamento="2023", genero="Aventura", comentario="linha1\nlinha2", data_inicio="01/06/2023",
            data_fim="30/06/2023", horas_jogadas="120", progresso="100%"))
        ctl.salvar_jogo(jogo("Hades", pc, wishlist=1))
        antes = [{k: v for k, v in dict(j).items() if k not in ("id", "id_console")} for j in ctl.listar_jogos()]
        caminho = os.path.join(self.pasta, "jogos.csv")
        self.assertEqual(ctl.exportar_csv(caminho), 2)

        db.CAMINHO_DB = os.path.join(self.pasta, "outro.db")
        db.cria_tabelas()
        self.assertEqual(ctl.importar_csv(caminho), (2, 0, []))
        depois = [{k: v for k, v in dict(j).items() if k not in ("id", "id_console")} for j in ctl.listar_jogos()]
        self.assertEqual(depois, antes)
        self.assertEqual([c["nome"] for c in ctl.buscar_consoles()], ["PC", "PS5"])
        self.assertEqual(ctl.importar_csv(caminho), (0, 2, []))  # importar de novo não duplica

    def test_linhas_invalidas_sao_relatadas_e_as_boas_entram(self):
        caminho = os.path.join(self.pasta, "manual.csv")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("Nome,Plataforma,Status,Avaliação\nHades,PC,zerado,9\nRuim,PC,,99\n,PC,,\nSem plataforma,,,\n,,,\n")
        importados, duplicados, erros = ctl.importar_csv(caminho)
        self.assertEqual((importados, duplicados, len(erros)), (1, 0, 3))
        self.assertTrue(erros[0].startswith("Linha 3:") and "maior que 10" in erros[0], erros)
        j = ctl.listar_jogos()[0]
        self.assertEqual((j["nome"], j["status"], j["avaliacao"]), ("Hades", "Zerado", 9))

    def test_arquivo_sem_as_colunas_obrigatorias(self):
        caminho = os.path.join(self.pasta, "errado.csv")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write("a;b\n1;2\n")
        with self.assertRaises(ctl.ErroValidacao):
            ctl.importar_csv(caminho)


if __name__ == "__main__":
    unittest.main()
