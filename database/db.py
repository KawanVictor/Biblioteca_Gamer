import sqlite3

def conecta():
    return sqlite3.connect("biblioteca_gamer.db")

def cria_tabelas():
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
                wishlist INTEGER DEFAULT 0,
                backlog INTEGER DEFAULT 0,
                data_inicio TEXT,
                data_fim TEXT,
                horas_jogadas INTEGER,
                progresso TEXT,
                FOREIGN KEY(id_console) REFERENCES consoles(id)
            );
        """)

def cadastrar_console(nome_console):
    if not nome_console.strip():
        return False
    try:
        with conecta() as conn:
            conn.execute("INSERT INTO consoles (nome) VALUES (?)", (nome_console.strip(),))
        return True
    except sqlite3.IntegrityError:
        return False

def buscar_consoles():
    with conecta() as conn:
        return conn.execute("SELECT id, nome FROM consoles ORDER BY nome").fetchall()

def cadastrar_jogo(
    nome, id_console, status, avaliacao, comentario, favorito, ano, genero,
    wishlist, backlog, data_inicio, data_fim, horas_jogadas, progresso
):
    with conecta() as conn:
        conn.execute("""
            INSERT INTO jogos (
                nome, id_console, status, avaliacao, comentario, favorito, ano_lancamento,
                genero, wishlist, backlog, data_inicio, data_fim, horas_jogadas, progresso
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nome.strip(), id_console,
            status.strip() if status else None,
            avaliacao,
            comentario.strip() if comentario else "",
            favorito,
            ano,
            genero.strip() if genero else "",
            wishlist,
            backlog,
            data_inicio,
            data_fim,
            horas_jogadas,
            progresso.strip() if progresso else ""
        ))

def listar_jogos(
    filtro_console=None, filtro_status=None, apenas_favoritos=False,
    apenas_wishlist=False, apenas_backlog=False
):
    query = """
        SELECT
            jogos.id,
            jogos.nome,
            consoles.nome,
            jogos.status,
            jogos.avaliacao,
            jogos.favorito,
            jogos.wishlist,
            jogos.backlog,
            jogos.data_inicio,
            jogos.data_fim,
            jogos.horas_jogadas,
            jogos.progresso
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
    if filtros:
        query += " WHERE " + " AND ".join(filtros)
    query += " ORDER BY jogos.nome"
    with conecta() as conn:
        return conn.execute(query, params).fetchall()

def remover_jogo(id_jogo):
    with conecta() as conn:
        conn.execute("DELETE FROM jogos WHERE id = ?", (id_jogo,))

def remover_console(id_console):
    with conecta() as conn:
        conn.execute("DELETE FROM jogos WHERE id_console = ?", (id_console,))
        conn.execute("DELETE FROM consoles WHERE id = ?", (id_console,))

def atualizar_jogo(
    id_jogo, nome, id_console, status, avaliacao, comentario, favorito, ano, genero,
    wishlist, backlog, data_inicio, data_fim, horas_jogadas, progresso
):
    with conecta() as conn:
        conn.execute("""
            UPDATE jogos
            SET nome=?, id_console=?, status=?, avaliacao=?, comentario=?, favorito=?, ano_lancamento=?, genero=?,
                wishlist=?, backlog=?, data_inicio=?, data_fim=?, horas_jogadas=?, progresso=?
            WHERE id=?
        """, (
            nome.strip(), id_console,
            status.strip() if status else None,
            avaliacao,
            comentario.strip() if comentario else "",
            favorito,
            ano,
            genero.strip() if genero else "",
            wishlist, backlog, data_inicio, data_fim, horas_jogadas, progresso.strip() if progresso else "",
            id_jogo
        ))

def ranking_favoritos(top_n=5):
    with conecta() as conn:
        return conn.execute("""
            SELECT jogos.nome, consoles.nome, jogos.avaliacao
            FROM jogos
            LEFT JOIN consoles ON jogos.id_console = consoles.id
            WHERE jogos.favorito = 1
            ORDER BY jogos.avaliacao DESC
            LIMIT ?
        """, (top_n,)).fetchall()
