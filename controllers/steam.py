"""
Consultas à Steam: busca e detalhes de jogos (loja, sem chave) e biblioteca de uma conta (exige chave).
Todas as funções lançam ErroSteam com uma mensagem pronta para mostrar ao usuário.
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request

LOJA = "https://store.steampowered.com/api"
API = "https://api.steampowered.com"
CAPA_VERTICAL = "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/library_600x900.jpg"
PAGINA_CHAVE = "https://steamcommunity.com/dev/apikey"
TEMPO_LIMITE = 15


class ErroSteam(Exception):
    pass


def _baixar(url):
    pedido = urllib.request.Request(url, headers={"User-Agent": "BibliotecaGamer"})
    with urllib.request.urlopen(pedido, timeout=TEMPO_LIMITE) as resposta:
        return resposta.read()


def _json(url, parametros):
    try:
        return json.loads(_baixar(f"{url}?{urllib.parse.urlencode(parametros)}"))
    except urllib.error.HTTPError as erro:
        if erro.code in (401, 403):
            raise ErroSteam("A Steam recusou o acesso. Confira a chave da API.")
        raise ErroSteam(f"A Steam respondeu com erro {erro.code}.")
    except (urllib.error.URLError, TimeoutError, OSError):
        raise ErroSteam("Não foi possível conectar à Steam. Verifique a internet.")
    except ValueError:
        raise ErroSteam("A Steam devolveu uma resposta inesperada.")


def buscar_jogos(termo):
    """Jogos da loja cujo nome combina com o termo: lista de {'appid', 'nome'} (no máximo 10)."""
    dados = _json(f"{LOJA}/storesearch/", {"term": termo.strip(), "l": "brazilian", "cc": "BR"})
    return [{"appid": item["id"], "nome": item["name"]} for item in dados.get("items", []) if item.get("type") == "app"]


def detalhes(appid):
    """Ano de lançamento, gêneros e imagem de um jogo: {'ano', 'genero', 'imagem'} (o que faltar vem None/'')."""
    dados = _json(f"{LOJA}/appdetails", {"appids": appid, "l": "brazilian", "cc": "BR"}).get(str(appid), {})
    if not dados.get("success"):
        raise ErroSteam("A Steam não tem detalhes desse jogo.")
    dados = dados["data"]
    ano = re.search(r"\b(19|20)\d{2}\b", dados.get("release_date", {}).get("date", ""))
    generos = [g["description"] for g in dados.get("genres", [])]
    return {
        "ano": int(ano.group()) if ano else None,
        "genero": ", ".join(generos[:2]),
        "imagem": dados.get("header_image"),
    }


def baixar_capa(appid, imagem_reserva=None):
    """Bytes da capa: a vertical da biblioteca ou, se o jogo não tiver, a imagem de reserva (URL). None se nenhuma existir."""
    for url in (CAPA_VERTICAL.format(appid=appid), imagem_reserva):
        if not url:
            continue
        try:
            return _baixar(url)
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
    return None


def biblioteca(chave, steam_id):
    """Jogos de uma conta: lista de {'appid', 'nome', 'horas'}. O perfil precisa ter 'Detalhes dos jogos' público."""
    chave, steam_id = chave.strip(), steam_id.strip()
    if not chave or not steam_id:
        raise ErroSteam("Informe a chave da API e o SteamID.")
    if not re.fullmatch(r"\d{17}", steam_id):
        raise ErroSteam("O SteamID são os 17 números do seu perfil (steamID64).")
    dados = _json(f"{API}/IPlayerService/GetOwnedGames/v1/", {
        "key": chave, "steamid": steam_id, "include_appinfo": 1, "include_played_free_games": 1, "format": "json"
    }).get("response", {})
    if "games" not in dados:
        raise ErroSteam("A Steam não devolveu jogos. Deixe 'Detalhes dos jogos' como público na privacidade do perfil.")
    return [
        {"appid": j["appid"], "nome": j.get("name") or f"App {j['appid']}", "horas": round(j.get("playtime_forever", 0) / 60)}
        for j in dados["games"]
    ]
