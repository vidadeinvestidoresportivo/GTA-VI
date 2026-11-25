"""Agente 3: editor de vídeo.

Junta o seu gameplay com a sua narração e gera:
- saida/<projeto>_longo.mp4   (16:9, 1920x1080) + saida/<projeto>_longo.srt (legenda para o YouTube)
- saida/<projeto>_short.mp4   (9:16, 1080x1920) com legendas grandes queimadas no vídeo
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import legendas
from .util import EXT_AUDIO, EXT_VIDEO, ErroCanal, info_midia, rodar_ffmpeg

LONGO = (1920, 1080)
SHORT = (1080, 1920)


@dataclass
class OpcoesEdicao:
    formatos: tuple[str, ...] = ("short", "longo")
    estilo_short: str = "corte"  # "corte" (tela cheia) ou "desfocado" (jogo inteiro + fundo borrado)
    volume_jogo: float = 0.15  # som do jogo por baixo da narração (0 = mudo, 1 = original)
    inicio_short: float = 0.0  # pular N segundos do começo do gameplay no Short
    inicio_longo: float = 0.0
    max_short: float = 60.0
    legenda_short: bool = True
    srt_longo: bool = True
    modelo_whisper: str = "small"
    fps: int = 60
    qualidade: int = 20  # CRF do x264: menor = melhor e maior arquivo (18 a 23 é bom)


def _arquivos(pasta: Path, exts: set[str]) -> list[Path]:
    return sorted(
        p
        for p in pasta.iterdir()
        if p.is_file() and p.suffix.lower() in exts and not p.name.startswith(".")
    )


def achar_gameplays(pasta: Path) -> list[Path]:
    videos = _arquivos(pasta, EXT_VIDEO)
    if not videos:
        raise ErroCanal(
            f"Nenhum vídeo de gameplay na pasta {pasta}.\n"
            "Coloque lá o arquivo gravado (.mp4, .mkv, .mov...)."
        )
    return videos


def achar_narracao(pasta: Path, formato: str) -> Path | None:
    audios = _arquivos(pasta, EXT_AUDIO)
    for nome in (f"narracao_{formato}", f"narração_{formato}", "narracao", "narração"):
        for a in audios:
            if a.stem.lower() == nome:
                return a
    outros = [a for a in audios if not a.stem.lower().startswith(("narracao_", "narração_"))]
    return outros[0] if len(outros) == 1 else None


def _filtro_escala(formato: str, estilo: str, rotulo_in: str, rotulo_out: str, idx: int) -> str:
    if formato == "longo":
        w, h = LONGO
        return (
            f"[{rotulo_in}]scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1[{rotulo_out}]"
        )
    w, h = SHORT
    if estilo == "desfocado":
        return (
            f"[{rotulo_in}]split[bg{idx}][fg{idx}];"
            f"[bg{idx}]scale={w // 4}:{h // 4}:force_original_aspect_ratio=increase,"
            f"crop={w // 4}:{h // 4},boxblur=8:2,scale={w}:{h}[bgb{idx}];"
            f"[fg{idx}]scale={w}:-2[fgs{idx}];"
            f"[bgb{idx}][fgs{idx}]overlay=(W-w)/2:(H-h)/2,setsar=1[{rotulo_out}]"
        )
    return (
        f"[{rotulo_in}]scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},setsar=1[{rotulo_out}]"
    )


def renderizar(
    pasta: Path,
    formato: str,
    gameplays: list[Path],
    narracao: Path | None,
    op: OpcoesEdicao,
) -> Path:
    saida_dir = pasta / "saida"
    saida_dir.mkdir(exist_ok=True)
    nome = pasta.name
    destino = saida_dir / f"{nome}_{formato}.mp4"
    inicio = op.inicio_short if formato == "short" else op.inicio_longo

    infos = [info_midia(g) for g in gameplays]
    total_gameplay = sum(i["duracao"] for i in infos) - inicio
    if total_gameplay <= 0.5:
        raise ErroCanal("O início escolhido é depois do fim do gameplay.")

    if narracao:
        dur_narr = info_midia(narracao)["duracao"]
        duracao = dur_narr + 0.6
    else:
        duracao = total_gameplay
    if formato == "short" and duracao > op.max_short:
        print(
            f"  Aviso: o Short teria {duracao:.0f}s; cortando em {op.max_short:.0f}s. "
            "Grave uma narração mais curta para o Short (narracao_short)."
        )
        duracao = op.max_short
    if total_gameplay < duracao:
        print(
            f"  Aviso: o gameplay ({total_gameplay:.0f}s) é mais curto que a narração "
            f"({duracao:.0f}s). A última imagem vai ficar parada no final."
        )

    entradas: list[str] = []
    for g in gameplays:
        entradas += ["-i", str(g)]
    idx_narr = None
    if narracao:
        idx_narr = len(gameplays)
        entradas += ["-i", str(narracao)]

    partes = []
    concat_in = []
    for i, info in enumerate(infos):
        corte_v = f"trim=start={inicio},setpts=PTS-STARTPTS," if i == 0 and inicio > 0 else ""
        corte_a = f"atrim=start={inicio},asetpts=PTS-STARTPTS," if i == 0 and inicio > 0 else ""
        partes.append(f"[{i}:v]{corte_v}fps={op.fps},format=yuv420p[v{i}raw]")
        partes.append(_filtro_escala(formato, op.estilo_short, f"v{i}raw", f"v{i}", i))
        if info["tem_audio"]:
            partes.append(
                f"[{i}:a]{corte_a}aresample=48000,aformat=channel_layouts=stereo[a{i}]"
            )
        else:
            dur = info["duracao"] - (inicio if i == 0 else 0)
            partes.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={dur:.3f}[a{i}]")
        concat_in.append(f"[v{i}][a{i}]")

    partes.append(f"{''.join(concat_in)}concat=n={len(gameplays)}:v=1:a=1[vcat][acat]")
    falta = max(0.0, duracao - total_gameplay) + 1
    partes.append(f"[vcat]tpad=stop_mode=clone:stop_duration={falta:.2f}[vpad]")

    ultimo_v = "vpad"
    if formato == "short" and op.legenda_short and narracao:
        palavras = legendas.transcrever(narracao, modelo=op.modelo_whisper)
        ass = saida_dir / "legendas_short.ass"
        legendas.gerar_ass_short(palavras, ass)
        # caminho relativo (o ffmpeg roda dentro da pasta do projeto): evita o problema do "C:" no Windows
        partes.append(f"[vpad]subtitles=saida/{ass.name}[vleg]")
        ultimo_v = "vleg"

    if narracao:
        vol_jogo = max(0.0, op.volume_jogo)
        partes.append(f"[acat]volume={vol_jogo},apad[ajogo]")
        partes.append(f"[{idx_narr}:a]aresample=48000,aformat=channel_layouts=stereo,apad[anarr]")
        partes.append(
            "[anarr][ajogo]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0,"
            "loudnorm=I=-14:TP=-1.5:LRA=11[aout]"
        )
    else:
        partes.append("[acat]apad,loudnorm=I=-14:TP=-1.5:LRA=11[aout]")

    args = [
        *entradas,
        "-filter_complex",
        ";".join(partes),
        "-map",
        f"[{ultimo_v}]",
        "-map",
        "[aout]",
        "-t",
        f"{duracao:.3f}",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        str(op.qualidade),
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-movflags",
        "+faststart",
        str(destino),
    ]
    print(f"\n  Gerando {formato.upper()} ({duracao:.0f}s)... isso pode levar alguns minutos.")
    rodar_ffmpeg(args, cwd=pasta)

    if formato == "longo" and op.srt_longo and narracao:
        palavras = legendas.transcrever(narracao, modelo=op.modelo_whisper)
        legendas.gerar_srt(palavras, saida_dir / f"{nome}_longo.srt")

    print(f"  Pronto: {destino}")
    return destino


def editar(pasta: Path, op: OpcoesEdicao | None = None) -> list[Path]:
    op = op or OpcoesEdicao()
    gameplays = achar_gameplays(pasta)
    print(f"Projeto: {pasta.name}")
    print("Gameplay: " + ", ".join(g.name for g in gameplays))
    feitos = []
    for formato in op.formatos:
        narracao = achar_narracao(pasta, formato)
        print(f"\n[{formato.upper()}] narração: {narracao.name if narracao else 'nenhuma (só som do jogo)'}")
        feitos.append(renderizar(pasta, formato, gameplays, narracao, op))
    return feitos
