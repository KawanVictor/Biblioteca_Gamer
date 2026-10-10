"""Desenha assets/icone.ico (um controle sobre fundo roxo). Rode de novo só se quiser mudar o ícone."""

import os

from PIL import Image, ImageDraw

LADO = 256
FUNDO, CONTROLE, DETALHE = "#6f42c1", "#ffffff", "#6f42c1"

img = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle((8, 8, 248, 248), radius=52, fill=FUNDO)
# corpo do controle: barra central e duas empunhaduras
d.rounded_rectangle((48, 88, 208, 164), radius=36, fill=CONTROLE)
d.ellipse((36, 100, 116, 196), fill=CONTROLE)
d.ellipse((140, 100, 220, 196), fill=CONTROLE)
# direcional
d.rounded_rectangle((70, 118, 106, 130), radius=4, fill=DETALHE)
d.rounded_rectangle((82, 106, 94, 142), radius=4, fill=DETALHE)
# botões
for x, y in ((158, 124), (186, 124), (172, 110), (172, 138)):
    d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=DETALHE)

destino = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icone.ico")
img.save(destino, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("gravado:", destino)
