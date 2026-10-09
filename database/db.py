"""
Acesso ao banco SQLite: esquema, migrações e consultas.
As consultas devolvem sqlite3.Row, então os campos são lidos pelo nome (jogo["nome"]).
"""

import os
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime

# Sempre ao lado do projeto, independente da pasta de onde o app é aberto.
CAMINHO_DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "biblioteca_gamer.db")

STATUS_JOGO = ["Não iniciado", "Jogando", "Pausado", "Zerado", "Abandonado"]
STATUS_PADRAO = "Jogando"

# Campos graváveis de um jogo, na ordem usada em INSERT/UPDATE.
CAMPOS_JOGO = (
    "nome", "id_console", "status", "avaliacao", "comentario", "favorito", "ano_lancamento",
    "genero", "wishlist", "backlog", "data_inicio", "data_fim", "horas_jogadas", "progresso"
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


# Uma função por versão do esquema. Para mudar o banco, acrescente _migrar_v2 etc. no fim da lista.
MIGRACOES = [_migrar_v1]


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


# ---------------------------------------------------------------- preferências

def ler_config(chave, padrao=None):
    with conecta() as conn:
        r = conn.execute("SELECT valor FROM config WHERE chave = ?", (chave,)).fetchone()
        return r["valor"] if r else padrao


def gravar_config(chave, valor):
    with conecta() as conn:
        conn.execute("INSERT OR REPLACE INTO config (chave, valor) VALUES (?, ?)", (chave, valor))
