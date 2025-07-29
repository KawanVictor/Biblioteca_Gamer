"""
Módulo de acesso ao banco de dados SQLite (database/db.py).
Gestão de conexão, criação de tabelas e operações CRUD.
"""
import sqlite3

def conecta():
    """
    Conecta ao banco de dados SQLite (arquivo local).
    """
    return sqlite3.connect("biblioteca_gamer.db")

def cria_tabelas():
    """
    Cria as tabelas consoles e jogos no banco, caso não existam.
    """
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
    Insere um novo console. Nome não pode ser vazio/duplicado.
    Retorna True se cadastrado, False caso já exista.
    """
    if not nome_console.strip():
        return False
    try:
        with conecta() as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO consoles (nome) VALUES (?)", (nome_console.strip(),))
        return True
    except sqlite3.IntegrityError:
        return False

def buscar_consoles():
    """
    Busca todos os consoles cadastrados.
    """
    with conecta() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id, nome FROM consoles ORDER BY nome")
        return cur.fetchall()

def cadastrar_jogo(nome, id_console, status, avaliacao, comentario, favorito, ano, genero):
    """
    Insere um novo jogo. Campos essenciais: nome, id_console.
    """
    with conecta() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO jogos
                (nome, id_console, status, avaliacao, comentario, favorito, ano_lancamento, genero)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nome.strip(),
            id_console,
            status.strip() if status else None,
            avaliacao,
            comentario.strip() if comentario else "",
            favorito,
            ano,
            genero.strip() if genero else ""
        ))

def listar_jogos(filtro_console=None, filtro_status=None, apenas_favoritos=False):
    """
    Busca jogos, podendo filtrar por console, status ou favoritos.
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
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()

def remover_jogo(id_jogo):
    """
    Remove um jogo pelo ID.
    """
    with conecta() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM jogos WHERE id = ?", (id_jogo,))

def remover_console(id_console):
    """
    Remove um console pelo ID e todos os jogos associados.
    """
    with conecta() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM jogos WHERE id_console = ?", (id_console,))
        cur.execute("DELETE FROM consoles WHERE id = ?", (id_console,))

def atualizar_jogo(id_jogo, nome, id_console, status, avaliacao, comentario, favorito, ano, genero):
    """
    Atualiza os dados de um jogo.
    """
    with conecta() as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE jogos
               SET nome=?, id_console=?, status=?, avaliacao=?, comentario=?,
                   favorito=?, ano_lancamento=?, genero=?
             WHERE id=?
        """, (
            nome.strip(),
            id_console,
            status.strip() if status else None,
            avaliacao,
            comentario.strip() if comentario else "",
            favorito,
            ano,
            genero.strip() if genero else "",
            id_jogo
        ))
