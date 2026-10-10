"""
Proteção de segredos (a chave da Steam) com a DPAPI do Windows: o valor gravado só pode ser
lido pelo mesmo usuário do Windows, na mesma máquina. Em outros sistemas não há proteção
disponível (DISPONIVEL = False) e quem chama decide não guardar o segredo.
"""

import base64
import ctypes
import sys

DISPONIVEL = sys.platform == "win32"
PREFIXO = "dpapi:"  # marca os valores protegidos, para distinguir de texto puro antigo


class _Blob(ctypes.Structure):
    _fields_ = [("tamanho", ctypes.c_uint32), ("dados", ctypes.POINTER(ctypes.c_char))]


def _dpapi(nome_funcao, dados):
    funcao = getattr(ctypes.windll.crypt32, nome_funcao)
    liberar = ctypes.windll.kernel32.LocalFree
    liberar.argtypes = [ctypes.c_void_p]
    area = ctypes.create_string_buffer(dados, len(dados))
    entrada = _Blob(len(dados), ctypes.cast(area, ctypes.POINTER(ctypes.c_char)))
    saida = _Blob()
    if not funcao(ctypes.byref(entrada), None, None, None, None, 0, ctypes.byref(saida)):
        raise OSError("a DPAPI recusou a operação")
    try:
        return ctypes.string_at(saida.dados, saida.tamanho)
    finally:
        liberar(ctypes.cast(saida.dados, ctypes.c_void_p))


def proteger(texto):
    """Texto -> valor protegido, pronto para gravar."""
    return PREFIXO + base64.b64encode(_dpapi("CryptProtectData", texto.encode("utf-8"))).decode("ascii")


def revelar(valor):
    """Valor protegido -> texto original. None se não der para ler (outro usuário, outra máquina, valor corrompido)."""
    try:
        return _dpapi("CryptUnprotectData", base64.b64decode(valor[len(PREFIXO):])).decode("utf-8")
    except (OSError, ValueError):
        return None
