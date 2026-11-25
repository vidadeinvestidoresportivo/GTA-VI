"""Agente 4: criador de thumbnails.

Tira alguns quadros do seu gameplay e monta thumbnails 1280x720 com texto grande,
contorno preto e um selo "GTA 6". Gera várias opções para você escolher a melhor.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

from .util import EXT_VIDEO, ErroCanal, achar_fonte, ffmpeg_exe, info_midia

import subprocess

LARGURA, ALTURA = 1280, 720
CORES_TEXTO = [(255, 255, 255), (255, 214, 0)]  # branco e amarelo, linha sim linha não
ROSA = (232, 30, 140)


def extrair_quadro(video: Path, segundo: float, destino: Path) -> Path:
    subprocess.run(
        [
            ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y",
            "-ss", f"{segundo:.2f}", "-i", str(video), "-frames:v", "1", str(destino),
        ],
        check=True,
    )
    if not destino.is_file():
        raise ErroCanal(f"Não consegui tirar um quadro de {video.name} em {segundo:.0f}s.")
    return destino


def _cobrir(img: Image.Image, w: int, h: int) -> Image.Image:
    escala = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * escala), round(img.height * escala)), Image.LANCZOS)
    x = (img.width - w) // 2
    y = (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def _quebrar(texto: str, fonte: ImageFont.FreeTypeFont, largura_max: int, desenho) -> list[str]:
    palavras = texto.split()
    linhas, atual = [], ""
    for p in palavras:
        teste = f"{atual} {p}".strip()
        if desenho.textlength(teste, font=fonte) <= largura_max or not atual:
            atual = teste
        else:
            linhas.append(atual)
            atual = p
    if atual:
        linhas.append(atual)
    return linhas


def _carregar_fonte(caminho: str | None, tamanho: int) -> ImageFont.FreeTypeFont:
    if caminho:
        return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default(size=tamanho)


def montar(fundo: Image.Image, texto: str, selo: str | None, destino: Path, lado: str = "esquerda") -> Path:
    img = _cobrir(fundo.convert("RGB"), LARGURA, ALTURA)
    img = ImageEnhance.Color(img).enhance(1.35)
    img = ImageEnhance.Contrast(img).enhance(1.15)

    # degradê escuro do lado do texto para dar leitura
    sombra = Image.new("L", (LARGURA, ALTURA), 0)
    ds = ImageDraw.Draw(sombra)
    for x in range(LARGURA):
        frac = x / LARGURA if lado == "direita" else 1 - x / LARGURA
        ds.line([(x, 0), (x, ALTURA)], fill=int(210 * max(0.0, frac - 0.25) / 0.75))
    preto = Image.new("RGB", (LARGURA, ALTURA), (0, 0, 0))
    img = Image.composite(preto, img, sombra)

    desenho = ImageDraw.Draw(img)
    caminho_fonte = achar_fonte()
    texto = texto.upper().strip()
    largura_max = int(LARGURA * 0.58)

    tamanho = 190
    while tamanho > 50:
        fonte = _carregar_fonte(caminho_fonte, tamanho)
        linhas = _quebrar(texto, fonte, largura_max, desenho)
        altura_linha = int(tamanho * 1.02)
        if len(linhas) <= 3 and altura_linha * len(linhas) <= ALTURA * 0.72:
            break
        tamanho -= 8

    contorno = max(4, tamanho // 14)
    y = (ALTURA - altura_linha * len(linhas)) // 2 + 20
    for i, linha in enumerate(linhas):
        largura_txt = desenho.textlength(linha, font=fonte)
        x = 60 if lado == "esquerda" else LARGURA - 60 - largura_txt
        desenho.text(
            (x, y), linha, font=fonte, fill=CORES_TEXTO[i % 2],
            stroke_width=contorno, stroke_fill=(0, 0, 0),
        )
        y += altura_linha

    if selo:
        fonte_selo = _carregar_fonte(caminho_fonte, 64)
        tw = desenho.textlength(selo.upper(), font=fonte_selo)
        caixa = Image.new("RGBA", (int(tw) + 50, 100), (0, 0, 0, 0))
        dc = ImageDraw.Draw(caixa)
        dc.rounded_rectangle([0, 0, caixa.width - 1, caixa.height - 1], radius=18, fill=ROSA + (255,))
        dc.text((25, 12), selo.upper(), font=fonte_selo, fill=(255, 255, 255),
                stroke_width=3, stroke_fill=(0, 0, 0))
        caixa = caixa.rotate(4, expand=True, resample=Image.BICUBIC)
        sombra_selo = caixa.split()[3].filter(ImageFilter.GaussianBlur(6))
        pos = (LARGURA - caixa.width - 30, 25) if lado == "esquerda" else (30, 25)
        img.paste((0, 0, 0), (pos[0] + 6, pos[1] + 8), sombra_selo)
        img.paste(caixa, pos, caixa)

    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino, quality=92)
    return destino


def gerar(
    pasta: Path,
    texto: str,
    selo: str | None = "GTA 6",
    tempos: list[float] | None = None,
    imagem: Path | None = None,
    lado: str = "esquerda",
) -> list[Path]:
    saida = pasta / "saida"
    saida.mkdir(exist_ok=True)
    feitos: list[Path] = []

    if imagem:
        feitos.append(montar(Image.open(imagem), texto, selo, saida / "thumb_1.jpg", lado))
    else:
        videos = sorted(
            p for p in pasta.iterdir() if p.is_file() and p.suffix.lower() in EXT_VIDEO
        )
        if not videos:
            raise ErroCanal("Sem gameplay na pasta para tirar a imagem. Use a opção --imagem.")
        video = videos[0]
        dur = info_midia(video)["duracao"]
        tempos = tempos or [dur * f for f in (0.12, 0.3, 0.5, 0.7, 0.88)]
        with tempfile.TemporaryDirectory() as tmp:
            for n, t in enumerate(tempos, 1):
                quadro = extrair_quadro(video, min(t, max(0, dur - 0.5)), Path(tmp) / f"q{n}.png")
                with Image.open(quadro) as fundo:
                    feitos.append(montar(fundo, texto, selo, saida / f"thumb_{n}.jpg", lado))

    print("Thumbnails criadas (escolha a melhor):")
    for f in feitos:
        print(f"  {f}")
    return feitos
