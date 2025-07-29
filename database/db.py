"""
database/db.py
Funções do banco: criar tabelas, CRUD de consoles e jogos.
"""

import sqlite3

def conecta():
    """Conecta ao banco SQLite local."""
    return sqlite3.connect("biblioteca_gamer.db")

def cria_tabelas():
    """Cria as tabelas consoles e jogos, se não existirem."""
    with conecta() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS consoles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL
            );
        """)
        cur.execute("""
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
                FOREIGN KEY(id_console) REFERENCES consoles(id)
            );
        """)

def cadastrar_console(nome_console):
    """
    Adiciona um console. Retorna True se ok, False se já existe ou nome vazio.
    """
    if not nome_console.strip():
        return False
    try:
        with conecta() as conn:
            conn.execute("INSERT INTO consoles (nome) VALUES (?)", (nome_console.strip(),))
        return True
    except sqlite3.IntegrityError:
        return False

def buscar_consoles():
    """Lista (id, nome) dos consoles cadastrados."""
    with conecta() as conn:
        return conn.execute("SELECT id, nome FROM consoles ORDER BY nome").fetchall()

def cadastrar_jogo(nome, id_console, status, avaliacao, comentario, favorito, ano, genero):
    """Adiciona novo jogo - nome e console obrigatórios."""
    with conecta() as conn:
        conn.execute("""
            INSERT INTO jogos (nome, id_console, status, avaliacao, comentario,
                               favorito, ano_lancamento, genero)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nome.strip(), id_console,
            status.strip() if status else None,
            avaliacao, comentario.strip() if comentario else "",
            favorito, ano, genero.strip() if genero else ""
        ))

def listar_jogos(filtro_console=None, filtro_status=None, apenas_favoritos=False):
    """
    Lista jogos cadastrados - permite filtrar por console, status, favoritos.
    Retorna lista de tuplas: (id, nome, nome_console, status, avaliacao, favorito)
    """
    query = """
        SELECT jogos.id, jogos.nome, consoles.nome, jogos.status, jogos.avaliacao, jogos.favorito
        FROM jogos
        LEFT JOIN consoles ON jogos.id_console = consoles.id
    """
    filtros = []
    params = []
    if filtro_console is not None:
        filtros.append("jogos.id_console = ?")
        params.append(filtro_console)
    if filtro_status:
        filtros.append("jogos.status = ?")
        params.append(filtro_status)
    if apenas_favoritos:
        filtros.append("jogos.favorito = 1")
    if filtros:
        query += " WHERE " + " AND ".join(filtros)
    query += " ORDER BY jogos.nome"
    with conecta() as conn:
        return conn.execute(query, params).fetchall()

def remover_jogo(id_jogo):
    """Remove jogo pelo ID."""
    with conecta() as conn:
        conn.execute("DELETE FROM jogos WHERE id = ?", (id_jogo,))

def remover_console(id_console):
    """Remove console e todos os jogos daquele console."""
    with conecta() as conn:
        conn.execute("DELETE FROM jogos WHERE id_console = ?", (id_console,))
        conn.execute("DELETE FROM consoles WHERE id = ?", (id_console,))

def atualizar_jogo(id_jogo, nome, id_console, status, avaliacao, comentario, favorito, ano, genero):
    """Atualiza dados de jogo pelo ID."""
    with conecta() as conn:
        conn.execute("""
            UPDATE jogos
               SET nome=?, id_console=?, status=?, avaliacao=?, comentario=?,
                   favorito=?, ano_lancamento=?, genero=?
             WHERE id=?
        """, (
            nome.strip(), id_console,
            status.strip() if status else None,
            avaliacao, comentario.strip() if comentario else "",
            favorito, ano, genero.strip() if genero else "",
            id_jogo
        ))
