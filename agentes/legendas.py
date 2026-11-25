"""Legendas automáticas a partir da SUA narração, usando o Whisper (roda grátis no PC).

- Short: legenda grande no meio da tela, 1 a 3 palavras por vez, palavra falada em amarelo.
- Vídeo longo: arquivo .srt para enviar ao YouTube (legenda que o espectador liga/desliga).
"""

from __future__ import annotations

import json
from pathlib import Path

AMARELO = "&H0000FFFF&"
BRANCO = "&H00FFFFFF&"


def transcrever(audio: Path, modelo: str = "small", idioma: str = "pt") -> list[dict]:
    """Devolve uma lista de palavras com início e fim (em segundos). Usa cache em JSON."""
    cache = audio.with_name(f".palavras_{audio.stem}_{modelo}.json")
    if cache.is_file() and cache.stat().st_mtime >= audio.stat().st_mtime:
        return json.loads(cache.read_text(encoding="utf-8"))

    from faster_whisper import WhisperModel

    print(f"  Transcrevendo sua voz com Whisper (modelo '{modelo}')...")
    print("  Na primeira vez ele baixa o modelo (~500 MB). Depois fica salvo.")
    whisper = WhisperModel(modelo, device="cpu", compute_type="int8")
    segmentos, _ = whisper.transcribe(
        str(audio), language=idioma, word_timestamps=True, vad_filter=True
    )
    palavras = []
    for seg in segmentos:
        for w in seg.words or []:
            texto = w.word.strip()
            if texto:
                palavras.append({"texto": texto, "inicio": float(w.start), "fim": float(w.end)})
        print(f"\r  Transcrito até {seg.end:6.1f}s", end="", flush=True)
    print()
    cache.write_text(json.dumps(palavras, ensure_ascii=False), encoding="utf-8")
    return palavras


def _agrupar(palavras: list[dict], max_palavras: int, max_chars: int) -> list[list[dict]]:
    grupos: list[list[dict]] = []
    atual: list[dict] = []
    for w in palavras:
        if atual:
            pausa = w["inicio"] - atual[-1]["fim"]
            chars = sum(len(x["texto"]) + 1 for x in atual) + len(w["texto"])
            pontuacao = atual[-1]["texto"][-1] in ".,!?;:"
            if len(atual) >= max_palavras or chars > max_chars or pausa > 0.6 or pontuacao:
                grupos.append(atual)
                atual = []
        atual.append(w)
    if atual:
        grupos.append(atual)
    return grupos


def _t_ass(s: float) -> str:
    s = max(0.0, s)
    h = int(s // 3600)
    m = int(s % 3600 // 60)
    return f"{h}:{m:02d}:{s % 60:05.2f}"


def _t_srt(s: float) -> str:
    s = max(0.0, s)
    ms = int(round(s * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    seg, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{seg:02d},{ms:03d}"


def _limpar(texto: str) -> str:
    return texto.replace("{", "(").replace("}", ")").replace("\\", "")


def gerar_ass_short(
    palavras: list[dict],
    destino: Path,
    largura: int = 1080,
    altura: int = 1920,
    deslocamento: float = 0.0,
    fonte: str = "Arial Black",
) -> Path:
    tamanho = int(altura * 0.05)
    cabecalho = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {largura}
PlayResY: {altura}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Padrao,{fonte},{tamanho},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,{max(4, tamanho // 12)},3,2,60,60,{int(altura * 0.30)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    eventos = []
    grupos = _agrupar(palavras, max_palavras=3, max_chars=22)
    for gi, grupo in enumerate(grupos):
        fim_grupo = grupo[-1]["fim"] + 0.25
        if gi + 1 < len(grupos):
            fim_grupo = min(fim_grupo, grupos[gi + 1][0]["inicio"])
        for i, w in enumerate(grupo):
            ini = w["inicio"]
            fim = grupo[i + 1]["inicio"] if i + 1 < len(grupo) else fim_grupo
            if fim <= ini:
                fim = ini + 0.05
            partes = []
            for j, x in enumerate(grupo):
                t = _limpar(x["texto"].upper())
                if j == i:
                    partes.append(f"{{\\c{AMARELO}\\fscx108\\fscy108}}{t}{{\\c{BRANCO}\\fscx100\\fscy100}}")
                else:
                    partes.append(t)
            eventos.append(
                f"Dialogue: 0,{_t_ass(ini + deslocamento)},{_t_ass(fim + deslocamento)},Padrao,,0,0,0,,"
                + " ".join(partes)
            )
    destino.write_text(cabecalho + "\n".join(eventos) + "\n", encoding="utf-8")
    return destino


def gerar_srt(palavras: list[dict], destino: Path, deslocamento: float = 0.0) -> Path:
    blocos = []
    for n, grupo in enumerate(_agrupar(palavras, max_palavras=12, max_chars=80), 1):
        texto = " ".join(w["texto"] for w in grupo)
        blocos.append(
            f"{n}\n{_t_srt(grupo[0]['inicio'] + deslocamento)} --> "
            f"{_t_srt(grupo[-1]['fim'] + deslocamento)}\n{texto}\n"
        )
    destino.write_text("\n".join(blocos), encoding="utf-8")
    return destino
