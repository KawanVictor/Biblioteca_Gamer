"""
Acesso ao banco SQLite: esquema, migrações e consultas.
As consultas devolvem sqlite3.Row, então os campos são lidos pelo nome (jogo["nome"]).
"""

import os
import shutil
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime

def _pasta_padrao():
    """Onde ficam banco, capas e backups, independente da pasta de onde o app é aberto."""
    pasta = os.environ.get("BIBLIOTECA_GAMER_DADOS")  # para escolher outro lugar, ex.: uma pasta do OneDrive
    if not pasta:
        if getattr(sys, "frozen", False):  # rodando como .exe: a pasta do programa é temporária
            pasta = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "BibliotecaGamer")
        else:
            pasta = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(pasta, exist_ok=True)
    return pasta


CAMINHO_DB = os.path.join(_pasta_padrao(), "biblioteca_gamer.db")
BACKUPS_MANTIDOS = 10


def pasta_dados(subpasta=None):
    """Pasta do banco, ou uma subpasta dela (criada se não existir)."""
    pasta = os.path.dirname(CAMINHO_DB)
    if subpasta:
        pasta = os.path.join(pasta, subpasta)
        os.makedirs(pasta, exist_ok=True)
    return pasta

STATUS_JOGO = ["Não iniciado", "Jogando", "Pausado", "Zerado", "Abandonado"]
STATUS_PADRAO = "Jogando"

# Campos graváveis de um jogo, na ordem usada em INSERT/UPDATE.
CAMPOS_JOGO = (
    "nome", "id_console", "status", "avaliacao", "comentario", "favorito", "ano_lancamento",
    "genero", "wishlist", "backlog", "data_inicio", "data_fim", "horas_jogadas", "progresso", "steam_appid"
)

FORMATOS_DATA = ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y")


@contextmanager
def conecta():
    """Abre a conexão, confirma (ou desfaz) a transação e fecha ao sair do with."""
    conn = sqlite3.connect(CAMINHO_DB)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


# ---------------------------------------------------------------- conversões

def normalizar_status(texto):
    """Converte status em texto livre (versões antigas, CSV) para um da lista; o que não reconhecer fica como está."""
    limpo = (texto or "").strip()
    for status in STATUS_JOGO:
        if status.lower() == limpo.lower():
            return status
    if "zerad" in limpo.lower():
        return "Zerado"
    return limpo


def data_para_iso(texto):
    """'25/12/2024' -> '2024-12-25'. Lança ValueError se não for uma data reconhecida."""
    texto = texto.strip()
    for formato in FORMATOS_DATA:
        try:
            return datetime.strptime(texto, formato).date().isoformat()
        except ValueError:
            pass
    raise ValueError(f"data inválida: {texto}")


def data_para_br(texto):
    """'2024-12-25' -> '25/12/2024'. Texto que não for data ISO volta como está."""
    if not texto:
        return ""
    try:
        return datetime.strptime(texto, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return texto


# ---------------------------------------------------------------- esquema e migrações

def _migrar_v1(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS consoles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jogos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            id_console INTEGER,
            status TEXT,
            avaliacao INTEGER,
            comentario TEXT,
            favorito INTEGER DEFAULT 0,
            ano_lancamento INTEGER,
            genero TEXT,
            wishlist INTEGER DEFAULT 0,
            backlog INTEGER DEFAULT 0,
            data_inicio TEXT,
            data_fim TEXT,
            horas_jogadas INTEGER,
            progresso TEXT,
            FOREIGN KEY(id_console) REFERENCES consoles(id)
        );
    """)
    conn.execute("CREATE TABLE IF NOT EXISTS config (chave TEXT PRIMARY KEY, valor TEXT);")
    # Bancos criados pelas primeiras versões do app podem não ter todas as colunas.
    colunas_novas = {
        "favorito": "INTEGER DEFAULT 0", "ano_lancamento": "INTEGER", "genero": "TEXT",
        "wishlist": "INTEGER DEFAULT 0", "backlog": "INTEGER DEFAULT 0", "data_inicio": "TEXT",
        "data_fim": "TEXT", "horas_jogadas": "INTEGER", "progresso": "TEXT", "comentario": "TEXT",
    }
    existentes = {c["name"] for c in conn.execute("PRAGMA table_info(jogos)")}
    for coluna, tipo in colunas_novas.items():
        if coluna not in existentes:
            conn.execute(f"ALTER TABLE jogos ADD COLUMN {coluna} {tipo}")
    # Status era texto livre e as datas eram DD/MM/AAAA: passa para a lista fixa e para ISO.
    for jogo in conn.execute("SELECT id, status, data_inicio, data_fim FROM jogos").fetchall():
        datas = []
        for valor in (jogo["data_inicio"], jogo["data_fim"]):
            try:
                datas.append(data_para_iso(valor) if valor and valor.strip() else None)
            except ValueError:
                datas.append(valor)  # não dá para interpretar: mantém o texto original
        conn.execute(
            "UPDATE jogos SET status = ?, data_inicio = ?, data_fim = ? WHERE id = ?",
            (normalizar_status(jogo["status"]) or None, datas[0], datas[1], jogo["id"])
        )


def _migrar_v2(conn):
    # Identificador do jogo na Steam: liga o jogo à capa e à importação da biblioteca.
    conn.execute("ALTER TABLE jogos ADD COLUMN steam_appid INTEGER")


# Uma função por versão do esquema. Para mudar o banco, acrescente _migrar_v3 etc. no fim da lista.
MIGRACOES = [_migrar_v1, _migrar_v2]


def fazer_backup():
    """
    Copia o banco para backups/ e apaga as cópias mais antigas, mantendo BACKUPS_MANTIDOS.
    Não faz nada se o banco está vazio ou não mudou desde o último backup. Devolve o caminho criado ou None.
    """
    if not os.path.exists(CAMINHO_DB):
        return None
    with conecta() as conn:
        if not conn.execute("SELECT 1 FROM consoles UNION ALL SELECT 1 FROM jogos LIMIT 1").fetchone():
            return None
    pasta = pasta_dados("backups")
    existentes = sorted(f for f in os.listdir(pasta) if f.startswith("biblioteca_gamer-") and f.endswith(".db"))
    if existentes and os.path.getmtime(os.path.join(pasta, existentes[-1])) >= os.path.getmtime(CAMINHO_DB):
        return None
    destino = os.path.join(pasta, f"biblioteca_gamer-{datetime.now():%Y%m%d-%H%M%S}.db")
    origem = sqlite3.connect(CAMINHO_DB)
    copia = sqlite3.connect(destino)
    try:
        origem.backup(copia)
    finally:
        copia.close(); origem.close()
    for antigo in (existentes + [os.path.basename(destino)])[:-BACKUPS_MANTIDOS]:
        os.remove(os.path.join(pasta, antigo))
    return destino


def cria_tabelas():
    """Cria o banco ou atualiza um banco antigo, aplicando só as migrações que faltam."""
    with conecta() as conn:
        versao = conn.execute("PRAGMA user_version").fetchone()[0]
        if versao >= len(MIGRACOES):
            return
        tem_dados = conn.execute("SELECT 1 FROM sqlite_master WHERE name = 'jogos'").fetchone()
    if tem_dados:
        base, ext = os.path.splitext(CAMINHO_DB)
        shutil.copy2(CAMINHO_DB, f"{base}.backup-v{versao}{ext}")
    with conecta() as conn:
        for numero, migrar in enumerate(MIGRACOES, start=1):
            if numero > versao:
                migrar(conn)
                conn.execute(f"PRAGMA user_version = {numero}")


# ---------------------------------------------------------------- consoles

def buscar_consoles():
    """Consoles em ordem alfabética, com a quantidade de jogos de cada um (total_jogos)."""
    with conecta() as conn:
        return conn.execute("""
            SELECT consoles.id, consoles.nome, COUNT(jogos.id) AS total_jogos
            FROM consoles
            LEFT JOIN jogos ON jogos.id_console = consoles.id
            GROUP BY consoles.id
            ORDER BY consoles.nome COLLATE NOCASE
        """).fetchall()


def existe_console(nome, ignorar_id=None):
    with conecta() as conn:
        return conn.execute(
            "SELECT 1 FROM consoles WHERE nome = ? COLLATE NOCASE AND id IS NOT ?", (nome, ignorar_id)
        ).fetchone() is not None


def cadastrar_console(nome):
    with conecta() as conn:
        return conn.execute("INSERT INTO consoles (nome) VALUES (?)", (nome,)).lastrowid


def renomear_console(id_console, nome):
    with conecta() as conn:
        conn.execute("UPDATE consoles SET nome = ? WHERE id = ?", (nome, id_console))


def remover_console(id_console):
    with conecta() as conn:
        conn.execute("DELETE FROM jogos WHERE id_console = ?", (id_console,))
        conn.execute("DELETE FROM consoles WHERE id = ?", (id_console,))


# ---------------------------------------------------------------- jogos

def cadastrar_jogo(campos):
    """campos: dicionário com as chaves de CAMPOS_JOGO."""
    with conecta() as conn:
        return conn.execute(
            f"INSERT INTO jogos ({', '.join(CAMPOS_JOGO)}) VALUES ({', '.join('?' * len(CAMPOS_JOGO))})",
            [campos[c] for c in CAMPOS_JOGO]
        ).lastrowid


def cadastrar_jogos(lista_campos):
    """Vários jogos em uma transação só (importações grandes)."""
    with conecta() as conn:
        conn.executemany(
            f"INSERT INTO jogos ({', '.join(CAMPOS_JOGO)}) VALUES ({', '.join('?' * len(CAMPOS_JOGO))})",
            [[campos[c] for c in CAMPOS_JOGO] for campos in lista_campos]
        )


def atualizar_jogo(id_jogo, campos):
    with conecta() as conn:
        conn.execute(
            f"UPDATE jogos SET {', '.join(c + ' = ?' for c in CAMPOS_JOGO)} WHERE id = ?",
            [campos[c] for c in CAMPOS_JOGO] + [id_jogo]
        )


def remover_jogo(id_jogo):
    with conecta() as conn:
        conn.execute("DELETE FROM jogos WHERE id = ?", (id_jogo,))


def existe_jogo(nome, id_console, ignorar_id=None):
    with conecta() as conn:
        return conn.execute(
            "SELECT 1 FROM jogos WHERE nome = ? COLLATE NOCASE AND id_console IS ? AND id IS NOT ?",
            (nome, id_console, ignorar_id)
        ).fetchone() is not None


def buscar_jogo(id_jogo):
    with conecta() as conn:
        return conn.execute("""
            SELECT jogos.*, consoles.nome AS console
            FROM jogos LEFT JOIN consoles ON jogos.id_console = consoles.id
            WHERE jogos.id = ?
        """, (id_jogo,)).fetchone()


def ids_jogos_do_console(id_console):
    with conecta() as conn:
        return [r[0] for r in conn.execute("SELECT id FROM jogos WHERE id_console = ?", (id_console,))]


def atualizar_dados_steam(id_jogo, steam_appid, horas_jogadas):
    """Usado pela importação da Steam em jogos que já existem: grava o appid e as horas, sem mexer no resto."""
    with conecta() as conn:
        conn.execute("UPDATE jogos SET steam_appid = ?, horas_jogadas = ? WHERE id = ?", (steam_appid, horas_jogadas, id_jogo))


def listar_jogos(
    filtro_console=None, filtro_status=None, apenas_favoritos=False,
    apenas_wishlist=False, apenas_backlog=False, busca_nome=None
):
    """Jogos em ordem alfabética; cada linha tem as colunas de jogos mais 'console' (nome da plataforma)."""
    query = """
        SELECT jogos.*, consoles.nome AS console
        FROM jogos
        LEFT JOIN consoles ON jogos.id_console = consoles.id
    """
    filtros, params = [], []
    if filtro_console is not None:
        filtros.append("jogos.id_console = ?"); params.append(filtro_console)
    if filtro_status:
        filtros.append("jogos.status = ?"); params.append(filtro_status)
    if apenas_favoritos:
        filtros.append("jogos.favorito = 1")
    if apenas_wishlist:
        filtros.append("jogos.wishlist = 1")
    if apenas_backlog:
        filtros.append("jogos.backlog = 1")
    if busca_nome and busca_nome.strip():
        filtros.append("jogos.nome LIKE ?"); params.append(f"%{busca_nome.strip()}%")
    if filtros:
        query += " WHERE " + " AND ".join(filtros)
    query += " ORDER BY jogos.nome COLLATE NOCASE"
    with conecta() as conn:
        return conn.execute(query, params).fetchall()


def contar_jogos():
    with conecta() as conn:
        return conn.execute("SELECT COUNT(*) FROM jogos").fetchone()[0]


def status_em_uso():
    """Status distintos gravados no banco (inclui os de versões antigas, fora da lista fixa)."""
    with conecta() as conn:
        return [r[0] for r in conn.execute(
            "SELECT DISTINCT status FROM jogos WHERE status IS NOT NULL AND status != '' ORDER BY status"
        )]


def resumo_progresso():
    """Devolve (zerados, total). Jogos da wishlist ficam de fora: ainda não fazem parte do acervo."""
    with conecta() as conn:
        r = conn.execute("""
            SELECT COALESCE(SUM(status = 'Zerado'), 0) AS zerados, COUNT(*) AS total
            FROM jogos
            WHERE COALESCE(wishlist, 0) = 0
        """).fetchone()
        return r["zerados"], r["total"]


def ranking_favoritos(top_n=5):
    """Favoritos da maior para a menor nota; os sem nota ficam por último."""
    with conecta() as conn:
        return conn.execute("""
            SELECT jogos.nome, consoles.nome AS console, jogos.avaliacao
            FROM jogos
            LEFT JOIN consoles ON jogos.id_console = consoles.id
            WHERE jogos.favorito = 1
            ORDER BY jogos.avaliacao IS NULL, jogos.avaliacao DESC, jogos.nome COLLATE NOCASE
            LIMIT ?
        """, (top_n,)).fetchall()


def estatisticas():
    """Números da tela de estatísticas. A wishlist só entra na contagem 'wishlist': o resto é o acervo."""
    acervo = "COALESCE(jogos.wishlist, 0) = 0"
    with conecta() as conn:
        geral = conn.execute(f"""
            SELECT COUNT(*) AS jogos, COALESCE(SUM(horas_jogadas), 0) AS horas, AVG(avaliacao) AS nota_media,
                   COALESCE(SUM(status = 'Zerado'), 0) AS zerados, COALESCE(SUM(backlog = 1), 0) AS backlog,
                   COALESCE(SUM(favorito = 1), 0) AS favoritos
            FROM jogos WHERE {acervo}
        """).fetchone()
        return {
            **dict(geral),
            "wishlist": conn.execute("SELECT COUNT(*) FROM jogos WHERE wishlist = 1").fetchone()[0],
            "por_status": conn.execute(f"""
                SELECT COALESCE(NULLIF(status, ''), '(sem status)') AS status, COUNT(*) AS jogos
                FROM jogos WHERE {acervo} GROUP BY 1 ORDER BY jogos DESC, 1
            """).fetchall(),
            "por_plataforma": conn.execute(f"""
                SELECT consoles.nome AS console, COUNT(*) AS jogos, COALESCE(SUM(jogos.horas_jogadas), 0) AS horas
                FROM jogos JOIN consoles ON jogos.id_console = consoles.id
                WHERE {acervo} GROUP BY consoles.id ORDER BY horas DESC, jogos DESC, console
            """).fetchall(),
            "zerados_por_ano": conn.execute(f"""
                SELECT substr(data_fim, 1, 4) AS ano, COUNT(*) AS jogos
                FROM jogos WHERE {acervo} AND status = 'Zerado' AND data_fim GLOB '[0-9][0-9][0-9][0-9]-*'
                GROUP BY ano ORDER BY ano DESC
            """).fetchall(),
            "por_genero": conn.execute(f"""
                SELECT genero, COUNT(*) AS jogos, AVG(avaliacao) AS nota_media
                FROM jogos WHERE {acervo} AND COALESCE(genero, '') != ''
                GROUP BY genero COLLATE NOCASE ORDER BY jogos DESC, genero LIMIT 10
            """).fetchall(),
            "mais_jogados": conn.execute(f"""
                SELECT jogos.nome, consoles.nome AS console, jogos.horas_jogadas AS horas
                FROM jogos LEFT JOIN consoles ON jogos.id_console = consoles.id
                WHERE {acervo} AND jogos.horas_jogadas > 0 ORDER BY horas DESC, jogos.nome LIMIT 5
            """).fetchall(),
        }


# ---------------------------------------------------------------- preferências

def ler_config(chave, padrao=None):
    with conecta() as conn:
        r = conn.execute("SELECT valor FROM config WHERE chave = ?", (chave,)).fetchone()
        return r["valor"] if r else padrao


def gravar_config(chave, valor):
    with conecta() as conn:
        conn.execute("INSERT OR REPLACE INTO config (chave, valor) VALUES (?, ?)", (chave, valor))
