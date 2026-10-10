"""
Controlador: regras e validações entre a interface e o banco.
A interface manda os valores como o usuário digitou; aqui eles são validados e convertidos.
"""

import csv
import io
import os
from datetime import date

from PIL import Image, UnidentifiedImageError

from controllers import steam
from controllers.steam import ErroSteam
from database import db
# Repassados para a interface, que só conversa com este módulo.
from database.db import (  # noqa: F401
    STATUS_JOGO, STATUS_PADRAO, cria_tabelas, buscar_consoles, buscar_jogo,
    listar_jogos, contar_jogos, status_em_uso, resumo_progresso, estatisticas,
    ranking_favoritos, ler_config, gravar_config, data_para_br, fazer_backup
)

TAMANHO_CAPA = (300, 450)


class ErroValidacao(Exception):
    """Dado recusado; a mensagem é escrita para ser mostrada ao usuário."""


class JogoDuplicado(ErroValidacao):
    pass


# ---------------------------------------------------------------- validação

def _texto(valor):
    return str(valor).strip() if valor is not None else ""


def _inteiro(valor, campo, minimo=None, maximo=None):
    """Campo numérico opcional: vazio vira None."""
    texto = _texto(valor)
    if not texto:
        return None
    try:
        numero = int(texto)
    except ValueError:
        raise ErroValidacao(f"{campo} deve ser um número inteiro.")
    if minimo is not None and numero < minimo:
        raise ErroValidacao(f"{campo} não pode ser menor que {minimo}.")
    if maximo is not None and numero > maximo:
        raise ErroValidacao(f"{campo} não pode ser maior que {maximo}.")
    return numero


def _data(valor, campo):
    """Data opcional digitada como DD/MM/AAAA; devolve em ISO (AAAA-MM-DD) ou None."""
    texto = _texto(valor)
    if not texto:
        return None
    try:
        return db.data_para_iso(texto)
    except ValueError:
        raise ErroValidacao(f"{campo} deve estar no formato DD/MM/AAAA.")


def _marcado(valor):
    return 1 if _texto(valor).lower() in ("1", "sim", "s", "true", "x") else 0


def validar_jogo(campos, id_jogo=None):
    """Valida os valores crus do formulário (ou de uma linha de CSV) e devolve o dicionário pronto para o banco."""
    nome = _texto(campos.get("nome"))
    if not nome:
        raise ErroValidacao("Preencha o nome do jogo.")
    id_console = campos.get("id_console")
    if id_console is None:
        raise ErroValidacao("Escolha uma plataforma cadastrada.")
    data_inicio = _data(campos.get("data_inicio"), "Data de início")
    data_fim = _data(campos.get("data_fim"), "Data de fim")
    if data_inicio and data_fim and data_fim < data_inicio:
        raise ErroValidacao("A data de fim não pode ser anterior à data de início.")
    limpo = {
        "nome": nome,
        "id_console": id_console,
        "status": db.normalizar_status(campos.get("status")) or STATUS_PADRAO,
        "avaliacao": _inteiro(campos.get("avaliacao"), "Avaliação", 1, 10),
        "comentario": _texto(campos.get("comentario")),
        "favorito": _marcado(campos.get("favorito")),
        "ano_lancamento": _inteiro(campos.get("ano_lancamento"), "Ano de lançamento", 1950, date.today().year + 5),
        "genero": _texto(campos.get("genero")),
        "wishlist": _marcado(campos.get("wishlist")),
        "backlog": _marcado(campos.get("backlog")),
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "horas_jogadas": _inteiro(campos.get("horas_jogadas"), "Horas jogadas", 0),
        "progresso": _texto(campos.get("progresso")),
        "steam_appid": _inteiro(campos.get("steam_appid"), "Steam AppID", 1),
    }
    if db.existe_jogo(nome, id_console, ignorar_id=id_jogo):
        raise JogoDuplicado(f"'{nome}' já está cadastrado nessa plataforma.")
    return limpo


def salvar_jogo(campos, id_jogo=None):
    """Cadastra (id_jogo=None) ou atualiza um jogo. Lança ErroValidacao se algum campo for recusado."""
    limpo = validar_jogo(campos, id_jogo)
    if id_jogo is None:
        return db.cadastrar_jogo(limpo)
    db.atualizar_jogo(id_jogo, limpo)
    return id_jogo


def salvar_console(nome, id_console=None):
    """Cadastra (id_console=None) ou renomeia uma plataforma."""
    nome = _texto(nome)
    if not nome:
        raise ErroValidacao("Preencha o nome da plataforma.")
    if db.existe_console(nome, ignorar_id=id_console):
        raise ErroValidacao(f"A plataforma '{nome}' já existe.")
    if id_console is None:
        return db.cadastrar_console(nome)
    db.renomear_console(id_console, nome)
    return id_console


def remover_jogo(id_jogo):
    db.remover_jogo(id_jogo)
    remover_capa(id_jogo)


def remover_console(id_console):
    """Remove a plataforma e os jogos dela (com as capas)."""
    ids_jogos = db.ids_jogos_do_console(id_console)
    db.remover_console(id_console)
    for id_jogo in ids_jogos:
        remover_capa(id_jogo)


# ---------------------------------------------------------------- capas

def caminho_capa(id_jogo):
    """Arquivo da capa do jogo (capas/<id>.jpg na pasta de dados). Pode não existir."""
    return os.path.join(db.pasta_dados("capas"), f"{id_jogo}.jpg")


def tem_capa(id_jogo):
    return os.path.exists(caminho_capa(id_jogo))


def salvar_capa(id_jogo, imagem):
    """imagem: caminho de um arquivo ou os bytes da imagem. É reduzida e gravada como JPEG."""
    try:
        with Image.open(io.BytesIO(imagem) if isinstance(imagem, bytes) else imagem) as img:
            img = img.convert("RGB")
            img.thumbnail(TAMANHO_CAPA)
            img.save(caminho_capa(id_jogo), "JPEG", quality=88)
    except (UnidentifiedImageError, OSError):
        raise ErroValidacao("O arquivo escolhido não é uma imagem válida.")


def remover_capa(id_jogo):
    if tem_capa(id_jogo):
        os.remove(caminho_capa(id_jogo))


# ---------------------------------------------------------------- Steam

def buscar_na_steam(nome):
    """Jogos da loja Steam com esse nome: lista de {'appid', 'nome'}. Lança ErroSteam."""
    if not _texto(nome):
        raise ErroSteam("Digite o nome do jogo antes de buscar.")
    return steam.buscar_jogos(nome)


def dados_da_steam(appid):
    """Ano, gênero e capa (bytes ou None) de um jogo da Steam, para preencher o formulário."""
    dados = steam.detalhes(appid)
    return {"ano": dados["ano"], "genero": dados["genero"], "capa": steam.baixar_capa(appid, dados["imagem"])}


def baixar_capa_da_steam(id_jogo):
    """Baixa a capa de um jogo que tem Steam AppID e ainda está sem capa. Devolve True se gravou."""
    jogo = buscar_jogo(id_jogo)
    if jogo is None or not jogo["steam_appid"] or tem_capa(id_jogo):
        return False
    imagem = steam.baixar_capa(jogo["steam_appid"])
    if imagem is None:
        return False
    try:
        salvar_capa(id_jogo, imagem)
    except ErroValidacao:
        return False
    return True


def importar_steam(chave, steam_id, id_console):
    """
    Traz a biblioteca de uma conta Steam para a plataforma indicada. Jogos novos entram com as horas
    jogadas; os que já existem (mesmo appid ou mesmo nome) só têm as horas e o appid atualizados.
    Devolve (novos, atualizados). Lança ErroSteam.
    """
    jogos_steam = steam.biblioteca(chave, steam_id)
    existentes = listar_jogos(filtro_console=id_console)
    por_appid = {j["steam_appid"]: j for j in existentes if j["steam_appid"]}
    por_nome = {j["nome"].casefold(): j for j in existentes}
    novos, atualizados = [], 0
    for item in jogos_steam:
        atual = por_appid.get(item["appid"]) or por_nome.get(item["nome"].casefold())
        if atual is None:
            campos = dict.fromkeys(db.CAMPOS_JOGO)
            campos.update(
                nome=item["nome"], id_console=id_console, steam_appid=item["appid"],
                horas_jogadas=item["horas"] or None, status="Jogando" if item["horas"] else "Não iniciado",
                comentario="", genero="", progresso="", favorito=0, wishlist=0, backlog=0
            )
            novos.append(campos)
            por_nome[item["nome"].casefold()] = campos  # a Steam às vezes repete o mesmo nome
        elif "id" in atual.keys():
            horas = max(item["horas"], atual["horas_jogadas"] or 0) or None
            if horas != atual["horas_jogadas"] or atual["steam_appid"] != item["appid"]:
                db.atualizar_dados_steam(atual["id"], item["appid"], horas)
                atualizados += 1
    db.cadastrar_jogos(novos)
    gravar_config("steam_chave", chave.strip()); gravar_config("steam_id", steam_id.strip())
    return len(novos), atualizados


# ---------------------------------------------------------------- exportar / importar CSV

# Cabeçalho do CSV -> campo do jogo ("console" é o nome da plataforma).
COLUNAS_CSV = {
    "Nome": "nome", "Plataforma": "console", "Status": "status", "Avaliação": "avaliacao",
    "Favorito": "favorito", "Wishlist": "wishlist", "Backlog": "backlog",
    "Ano de lançamento": "ano_lancamento", "Gênero": "genero", "Data início": "data_inicio",
    "Data fim": "data_fim", "Horas jogadas": "horas_jogadas", "Progresso": "progresso",
    "Comentário": "comentario", "Steam AppID": "steam_appid",
}
_CAMPOS_SIM_NAO = ("favorito", "wishlist", "backlog")
_CAMPOS_DATA = ("data_inicio", "data_fim")


def exportar_csv(caminho):
    """Grava todos os jogos em CSV (separador ';', abre direto no Excel). Devolve a quantidade exportada."""
    jogos = listar_jogos()
    with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.writer(arquivo, delimiter=";")
        escritor.writerow(COLUNAS_CSV)
        for jogo in jogos:
            linha = []
            for campo in COLUNAS_CSV.values():
                valor = jogo[campo]
                if campo in _CAMPOS_SIM_NAO:
                    valor = "Sim" if valor else "Não"
                elif campo in _CAMPOS_DATA:
                    valor = data_para_br(valor)
                linha.append("" if valor is None else valor)
            escritor.writerow(linha)
    return len(jogos)


def importar_csv(caminho):
    """
    Lê um CSV no formato do exportar_csv. Plataformas que não existem são criadas e jogos
    já cadastrados são pulados. Devolve (importados, duplicados, erros), com erros = lista de mensagens.
    """
    with open(caminho, newline="", encoding="utf-8-sig") as arquivo:
        cabecalho = arquivo.readline()
        arquivo.seek(0)
        separador = ";" if cabecalho.count(";") >= cabecalho.count(",") else ","
        linhas = list(csv.DictReader(arquivo, delimiter=separador))
    if not linhas or "Nome" not in linhas[0] or "Plataforma" not in linhas[0]:
        raise ErroValidacao("O arquivo precisa ter pelo menos as colunas 'Nome' e 'Plataforma'.")
    ids_consoles = {c["nome"].lower(): c["id"] for c in buscar_consoles()}
    importados, duplicados, erros = 0, 0, []
    for numero, linha in enumerate(linhas, start=2):  # linha 1 é o cabeçalho
        campos = {campo: linha.get(coluna) for coluna, campo in COLUNAS_CSV.items()}
        if not any(_texto(v) for v in campos.values()):
            continue
        try:
            plataforma = _texto(campos.pop("console"))
            if not plataforma:
                raise ErroValidacao("plataforma em branco.")
            if not _texto(campos["nome"]):
                raise ErroValidacao("nome em branco.")
            if plataforma.lower() not in ids_consoles:
                ids_consoles[plataforma.lower()] = db.cadastrar_console(plataforma)
            campos["id_console"] = ids_consoles[plataforma.lower()]
            salvar_jogo(campos)
            importados += 1
        except JogoDuplicado:
            duplicados += 1
        except ErroValidacao as erro:
            erros.append(f"Linha {numero}: {erro}")
    return importados, duplicados, erros
