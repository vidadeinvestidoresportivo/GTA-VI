"""Funções compartilhadas: localizar o ffmpeg, ler duração de mídia, achar fontes, etc."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_PROJETOS = RAIZ / "projetos"
PASTA_TENDENCIAS = RAIZ / "tendencias"

EXT_VIDEO = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv"}
EXT_AUDIO = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac", ".opus", ".wma"}


class ErroCanal(Exception):
    """Erro com mensagem amigável para mostrar ao usuário."""


def ffmpeg_exe() -> str:
    """Usa o ffmpeg instalado no sistema; se não houver, usa o que vem com o imageio-ffmpeg."""
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # pragma: no cover
        raise ErroCanal(
            "ffmpeg não encontrado. Rode o instalar.bat de novo ou instale com:\n"
            "  winget install Gyan.FFmpeg"
        ) from exc


def rodar_ffmpeg(args: list[str], cwd: Path | None = None) -> None:
    cmd = [ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-stats", "-y", *args]
    proc = subprocess.run(cmd, cwd=cwd)
    if proc.returncode != 0:
        raise ErroCanal("O ffmpeg falhou ao gerar o vídeo (veja a mensagem acima).")


def info_midia(caminho: Path) -> dict:
    """Lê duração, resolução e se tem áudio, a partir da saída do `ffmpeg -i`."""
    proc = subprocess.run(
        [ffmpeg_exe(), "-hide_banner", "-i", str(caminho)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    saida = proc.stderr
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", saida)
    if not m:
        raise ErroCanal(f"Não consegui ler o arquivo: {caminho.name}")
    h, mi, s = m.groups()
    duracao = int(h) * 3600 + int(mi) * 60 + float(s)
    largura = altura = None
    mv = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", saida)
    if mv:
        largura, altura = int(mv.group(1)), int(mv.group(2))
    return {
        "duracao": duracao,
        "largura": largura,
        "altura": altura,
        "tem_audio": "Audio:" in saida,
        "tem_video": "Video:" in saida,
    }


def slug(texto: str, limite: int = 50) -> str:
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    texto = re.sub(r"[^a-zA-Z0-9]+", "-", texto).strip("-").lower()
    return texto[:limite].strip("-") or "projeto"


def achar_fonte(preferidas: list[str] | None = None) -> str | None:
    """Procura uma fonte grossa (Impact no Windows) para thumbnails."""
    nomes = preferidas or [
        "impact.ttf",
        "Impact.ttf",
        "ariblk.ttf",
        "arialbd.ttf",
        "Anton-Regular.ttf",
        "DejaVuSans-Bold.ttf",
        "LiberationSans-Bold.ttf",
    ]
    pastas = [
        RAIZ / "fontes",
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts",
        Path("/usr/share/fonts"),
        Path("/Library/Fonts"),
        Path("/System/Library/Fonts"),
    ]
    for nome in nomes:
        for pasta in pastas:
            if not pasta.is_dir():
                continue
            direto = pasta / nome
            if direto.is_file():
                return str(direto)
            for achado in pasta.rglob(nome):
                return str(achado)
    return None


def resolver_projeto(nome: str) -> Path:
    """Aceita o nome da pasta do projeto ou um caminho completo."""
    p = Path(nome)
    if p.is_dir():
        return p.resolve()
    p = PASTA_PROJETOS / nome
    if p.is_dir():
        return p
    candidatos = [d for d in PASTA_PROJETOS.glob(f"*{nome}*") if d.is_dir()]
    if len(candidatos) == 1:
        return candidatos[0]
    raise ErroCanal(f"Projeto não encontrado: {nome}. Veja as pastas em {PASTA_PROJETOS}")


def listar_projetos() -> list[Path]:
    if not PASTA_PROJETOS.is_dir():
        return []
    return sorted(
        (d for d in PASTA_PROJETOS.iterdir() if d.is_dir()),
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )


def copiar_para_area_de_transferencia(texto: str) -> bool:
    try:
        if sys.platform.startswith("win"):
            subprocess.run("clip", input=texto.encode("utf-16-le"), check=True, shell=True)
            return True
        for cmd in (["pbcopy"], ["wl-copy"], ["xclip", "-selection", "clipboard"]):
            if shutil.which(cmd[0]):
                subprocess.run(cmd, input=texto.encode("utf-8"), check=True)
                return True
    except Exception:
        pass
    return False


def abrir_pasta(pasta: Path) -> None:
    try:
        if sys.platform.startswith("win"):
            os.startfile(pasta)  # type: ignore[attr-defined]
    except Exception:
        pass
