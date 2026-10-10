"""Banco e controlador: migração, validações, filtros e CSV."""

import io
import json
import os
import sqlite3
import unittest
import urllib.error
from unittest import mock

from PIL import Image

from controllers import controller as ctl
from controllers import segredo, steam
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
            "progresso": "100%", "steam_appid": None, "console": "PS5",
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
        ctl.salvar_jogo(jogo("Hades", pc, wishlist=1, steam_appid="1145360"))
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


class TesteBackup(TesteComBanco):
    def backups(self):
        pasta = os.path.join(self.pasta, "backups")
        return sorted(os.listdir(pasta)) if os.path.isdir(pasta) else []

    def test_banco_vazio_nao_gera_backup(self):
        self.assertIsNone(ctl.fazer_backup())
        self.assertEqual(self.backups(), [])

    def test_copia_o_banco_e_so_repete_se_algo_mudou(self):
        ctl.salvar_console("PC")
        caminho = ctl.fazer_backup()
        self.assertEqual(self.backups(), [os.path.basename(caminho)])
        copia = sqlite3.connect(caminho)
        self.assertEqual(copia.execute("SELECT nome FROM consoles").fetchall(), [("PC",)])
        copia.close()
        self.assertIsNone(ctl.fazer_backup())  # nada mudou desde a última cópia
        self.assertEqual(len(self.backups()), 1)

    def test_mantem_so_os_mais_recentes(self):
        ctl.salvar_console("PC")
        pasta = db.pasta_dados("backups")
        antigos = [f"biblioteca_gamer-2020010{n}-000000.db" for n in range(1, 4)]
        for nome in antigos:
            open(os.path.join(pasta, nome), "w").close()
            os.utime(os.path.join(pasta, nome), (0, 0))
        with mock.patch.object(db, "BACKUPS_MANTIDOS", 2):
            novo = os.path.basename(ctl.fazer_backup())
        self.assertEqual(self.backups(), [antigos[2], novo])


class TesteCapas(TesteComBanco):
    def setUp(self):
        super().setUp()
        self.pc = ctl.salvar_console("PC")
        self.imagem = os.path.join(self.pasta, "original.png")
        Image.new("RGBA", (1200, 1800), "red").save(self.imagem)

    def test_capa_e_reduzida_e_gravada_como_jpeg_na_pasta_de_dados(self):
        id_jogo = ctl.salvar_jogo(jogo())
        self.assertFalse(ctl.tem_capa(id_jogo))
        ctl.salvar_capa(id_jogo, self.imagem)
        self.assertEqual(ctl.caminho_capa(id_jogo), os.path.join(self.pasta, "capas", f"{id_jogo}.jpg"))
        with Image.open(ctl.caminho_capa(id_jogo)) as img:
            self.assertEqual((img.format, img.size), ("JPEG", (300, 450)))
        with open(self.imagem, "rb") as f:
            ctl.salvar_capa(id_jogo, f.read())  # também aceita os bytes (capa baixada)
        ctl.remover_capa(id_jogo); ctl.remover_capa(id_jogo)
        self.assertFalse(ctl.tem_capa(id_jogo))

    def test_arquivo_que_nao_e_imagem_e_recusado(self):
        id_jogo = ctl.salvar_jogo(jogo())
        with self.assertRaises(ctl.ErroValidacao):
            ctl.salvar_capa(id_jogo, __file__)
        with self.assertRaises(ctl.ErroValidacao):
            ctl.salvar_capa(id_jogo, b"isto nao e uma imagem")
        self.assertFalse(ctl.tem_capa(id_jogo))

    def test_remover_jogo_ou_plataforma_apaga_as_capas(self):
        ps5 = ctl.salvar_console("PS5")
        a, b, c = (ctl.salvar_jogo(jogo(n, i)) for n, i in (("A", self.pc), ("B", ps5), ("C", ps5)))
        for id_jogo in (a, b, c):
            ctl.salvar_capa(id_jogo, self.imagem)
        ctl.remover_jogo(a)
        self.assertEqual(sorted(os.listdir(os.path.join(self.pasta, "capas"))), [f"{b}.jpg", f"{c}.jpg"])
        ctl.remover_console(ps5)
        self.assertEqual(os.listdir(os.path.join(self.pasta, "capas")), [])


class TesteEstatisticas(TesteComBanco):
    def test_numeros_do_acervo(self):
        pc = ctl.salvar_console("PC"); ps5 = ctl.salvar_console("PS5"); ctl.salvar_console("Vazio")
        ctl.salvar_jogo(jogo("A", pc, status="Zerado", avaliacao="10", horas_jogadas="50", genero="RPG", data_fim="10/05/2024", favorito=1))
        ctl.salvar_jogo(jogo("B", pc, status="Zerado", avaliacao="8", horas_jogadas="20", genero="rpg", data_fim="01/01/2023"))
        ctl.salvar_jogo(jogo("C", ps5, status="Zerado", horas_jogadas="5", genero="Ação", data_fim="31/12/2024"))
        ctl.salvar_jogo(jogo("D", ps5, backlog=1))
        ctl.salvar_jogo(jogo("Desejo", ps5, wishlist=1, avaliacao="1", horas_jogadas="999", genero="RPG", status="Zerado", data_fim="01/01/2024"))
        e = ctl.estatisticas()
        self.assertEqual((e["jogos"], e["horas"], e["nota_media"], e["zerados"], e["backlog"], e["favoritos"], e["wishlist"]), (4, 75, 9.0, 3, 1, 1, 1))
        self.assertEqual([tuple(r) for r in e["por_status"]], [("Zerado", 3), ("Jogando", 1)])
        self.assertEqual([tuple(r) for r in e["por_plataforma"]], [("PC", 2, 70), ("PS5", 2, 5)])
        self.assertEqual([tuple(r) for r in e["zerados_por_ano"]], [("2024", 2), ("2023", 1)])
        self.assertEqual([tuple(r) for r in e["por_genero"]], [("RPG", 2, 9.0), ("Ação", 1, None)])
        self.assertEqual([tuple(r) for r in e["mais_jogados"]], [("A", "PC", 50), ("B", "PC", 20), ("C", "PS5", 5)])

    def test_banco_vazio(self):
        e = ctl.estatisticas()
        self.assertEqual((e["jogos"], e["horas"], e["nota_media"], e["zerados"], e["por_status"]), (0, 0, None, 0, []))


RESPOSTAS_STEAM = {
    "storesearch": {"total": 3, "items": [
        {"type": "app", "name": "Hades II", "id": 1145350}, {"type": "app", "name": "Hades", "id": 1145360},
        {"type": "bundle", "name": "Pacote Hades", "id": 7},
    ]},
    "appdetails": {"1145360": {"success": True, "data": {
        "name": "Hades", "release_date": {"coming_soon": False, "date": "17/set./2020"},
        "genres": [{"description": "Ação"}, {"description": "Indie"}, {"description": "RPG"}],
        "header_image": "https://exemplo/header.jpg",
    }}, "999": {"success": False}},
    "GetOwnedGames": {"response": {"game_count": 3, "games": [
        {"appid": 1145360, "name": "Hades", "playtime_forever": 3000},
        {"appid": 367520, "name": "Hollow Knight", "playtime_forever": 0},
        {"appid": 504230, "name": "Celeste", "playtime_forever": 95},
    ]}},
}


def steam_falsa(url):
    """Substitui o acesso à internet: devolve a resposta gravada do endpoint pedido."""
    if "library_600x900" in url:
        raise urllib.error.HTTPError(url, 404, "Not Found", None, None)
    if url.endswith(".jpg"):
        return b"bytes-da-imagem"
    return json.dumps(next(r for trecho, r in RESPOSTAS_STEAM.items() if trecho in url)).encode()


class TesteSteam(TesteComBanco):
    CHAVE, STEAM_ID = "ABC123", "76561198000000000"

    def setUp(self):
        super().setUp()
        self.pedidos = []
        def baixar(url):
            self.pedidos.append(url); return steam_falsa(url)
        remendo = mock.patch.object(steam, "_baixar", baixar)
        remendo.start(); self.addCleanup(remendo.stop)
        self.pc = ctl.salvar_console("PC")

    def test_busca_devolve_so_jogos(self):
        self.assertEqual(ctl.buscar_na_steam(" hades "), [{"appid": 1145350, "nome": "Hades II"}, {"appid": 1145360, "nome": "Hades"}])
        self.assertIn("term=hades&", self.pedidos[0])
        with self.assertRaises(ctl.ErroSteam):
            ctl.buscar_na_steam("  ")

    def test_detalhes_trazem_ano_generos_e_capa_de_reserva(self):
        self.assertEqual(ctl.dados_da_steam(1145360), {"ano": 2020, "genero": "Ação, Indie", "capa": b"bytes-da-imagem"})
        self.assertEqual(self.pedidos[-1], "https://exemplo/header.jpg")  # a vertical deu 404
        with self.assertRaises(ctl.ErroSteam):
            ctl.dados_da_steam(999)

    def test_erros_de_rede_viram_mensagens(self):
        casos = [
            (urllib.error.URLError("sem rede"), "internet"), (TimeoutError(), "internet"),
            (urllib.error.HTTPError("u", 403, "Forbidden", None, None), "chave"),
            (urllib.error.HTTPError("u", 500, "Erro", None, None), "erro 500"),
        ]
        for excecao, trecho in casos:
            with mock.patch.object(steam, "_baixar", side_effect=excecao), self.assertRaises(ctl.ErroSteam) as contexto:
                steam.biblioteca(self.CHAVE, self.STEAM_ID)
            self.assertIn(trecho, str(contexto.exception))
        with mock.patch.object(steam, "_baixar", return_value=b"<html>"), self.assertRaises(ctl.ErroSteam):
            steam.buscar_jogos("hades")

    def test_biblioteca_valida_os_dados_da_conta(self):
        for chave, steam_id in (("", self.STEAM_ID), (self.CHAVE, ""), (self.CHAVE, "meu-apelido"), (self.CHAVE, "123")):
            with self.assertRaises(ctl.ErroSteam):
                steam.biblioteca(chave, steam_id)
        self.assertEqual(self.pedidos, [])  # nem chega a consultar
        with mock.patch.dict(RESPOSTAS_STEAM, {"GetOwnedGames": {"response": {}}}), self.assertRaises(ctl.ErroSteam) as contexto:
            steam.biblioteca(self.CHAVE, self.STEAM_ID)
        self.assertIn("público", str(contexto.exception))

    def test_importar_cria_os_novos_e_atualiza_os_existentes(self):
        ctl.salvar_jogo(jogo("hades", self.pc, status="Zerado", avaliacao="9", horas_jogadas="10"))  # sem appid, menos horas
        ctl.salvar_jogo(jogo("Celeste", self.pc, horas_jogadas="40", steam_appid="504230"))         # mais horas que a Steam
        self.assertEqual(ctl.importar_steam(self.CHAVE, self.STEAM_ID, self.pc), (1, 1))
        jogos = {j["nome"]: (j["status"], j["horas_jogadas"], j["steam_appid"], j["avaliacao"]) for j in ctl.listar_jogos()}
        self.assertEqual(jogos, {
            "hades": ("Zerado", 50, 1145360, 9),              # só horas e appid mudaram
            "Celeste": ("Jogando", 40, 504230, None),          # horas maiores são mantidas
            "Hollow Knight": ("Não iniciado", None, 367520, None),
        })
        self.assertEqual(ctl.importar_steam(self.CHAVE, self.STEAM_ID, self.pc), (0, 0))  # repetir não muda nada
        self.assertEqual((ctl.ler_chave_steam(), ctl.ler_config("steam_id")), (self.CHAVE, self.STEAM_ID))

    @unittest.skipUnless(segredo.DISPONIVEL, "a proteção usa a DPAPI do Windows")
    def test_chave_e_guardada_protegida_e_nunca_em_texto_puro(self):
        ctl.guardar_chave_steam(self.CHAVE)
        gravado = ctl.ler_config("steam_chave")
        self.assertTrue(gravado.startswith(segredo.PREFIXO))
        with open(db.CAMINHO_DB, "rb") as arquivo:
            self.assertNotIn(self.CHAVE.encode(), arquivo.read())
        self.assertEqual(ctl.ler_chave_steam(), self.CHAVE)
        ctl.guardar_chave_steam("çhave com acento ✓")
        self.assertEqual(ctl.ler_chave_steam(), "çhave com acento ✓")

    @unittest.skipUnless(segredo.DISPONIVEL, "a proteção usa a DPAPI do Windows")
    def test_chave_antiga_em_texto_puro_e_protegida_ao_abrir_o_app(self):
        ctl.gravar_config("steam_chave", self.CHAVE)
        ctl.cria_tabelas()
        self.assertTrue(ctl.ler_config("steam_chave").startswith(segredo.PREFIXO))
        self.assertEqual(ctl.ler_chave_steam(), self.CHAVE)

    def test_valor_ilegivel_ou_ausente_devolve_vazio(self):
        self.assertEqual(ctl.ler_chave_steam(), "")
        ctl.gravar_config("steam_chave", segredo.PREFIXO + "isto-nao-e-um-valor-valido")
        self.assertEqual(ctl.ler_chave_steam(), "")

    def test_sem_protecao_disponivel_a_chave_nao_e_guardada(self):
        with mock.patch.object(segredo, "DISPONIVEL", False):
            ctl.guardar_chave_steam(self.CHAVE)
            self.assertEqual(ctl.ler_config("steam_chave"), "")
            ctl.gravar_config("steam_chave", self.CHAVE)  # texto puro de uma versão anterior
            ctl.cria_tabelas()
            self.assertEqual(ctl.ler_config("steam_chave"), "")
        self.assertEqual(ctl.ler_chave_steam(), "")

    def test_capa_que_falta_e_baixada_pelo_appid(self):
        com_appid = ctl.salvar_jogo(jogo("Hades", self.pc, steam_appid="1145360"))
        sem_appid = ctl.salvar_jogo(jogo("Outro", self.pc))
        imagem = io.BytesIO(); Image.new("RGB", (600, 900), "blue").save(imagem, "JPEG")
        with mock.patch.object(steam, "baixar_capa", return_value=imagem.getvalue()) as baixar:
            self.assertTrue(ctl.baixar_capa_da_steam(com_appid))
            self.assertFalse(ctl.baixar_capa_da_steam(com_appid))  # já tem capa
            self.assertFalse(ctl.baixar_capa_da_steam(sem_appid))
            self.assertEqual(baixar.call_count, 1)
        self.assertTrue(ctl.tem_capa(com_appid))
        with mock.patch.object(steam, "baixar_capa", return_value=None):
            ctl.remover_capa(com_appid)
            self.assertFalse(ctl.baixar_capa_da_steam(com_appid))  # a Steam não tem imagem


if __name__ == "__main__":
    unittest.main()
