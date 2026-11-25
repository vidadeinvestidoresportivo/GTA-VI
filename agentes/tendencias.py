"""Agente 1: caçador de tendências.

Fontes gratuitas, sem chave de API:
- Sugestões de busca do YouTube (o que as pessoas digitam na barra de busca).
- Google Trends (buscas em alta relacionadas a GTA 6 no Brasil).

O resultado vai para a tela e para tendencias/AAAA-MM-DD.md.
"""

from __future__ import annotations

import datetime as dt
import string
import time
from collections import defaultdict

import requests

from .util import PASTA_TENDENCIAS

URL_SUGESTOES = "https://suggestqueries.google.com/complete/search"
CABECALHO = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def sugestoes_youtube(termo: str, idioma: str = "pt", pais: str = "BR") -> list[str]:
    params = {"client": "firefox", "ds": "yt", "hl": idioma, "gl": pais, "q": termo}
    try:
        r = requests.get(URL_SUGESTOES, params=params, headers=CABECALHO, timeout=10)
        r.raise_for_status()
        dados = r.json()
        return [s for s in dados[1] if isinstance(s, str)]
    except Exception:
        return []


def coletar_youtube(sementes: list[str], expandir: bool = True) -> list[tuple[str, int]]:
    """Pontua cada sugestão pela posição em que aparece (1º lugar vale mais)."""
    pontos: dict[str, int] = defaultdict(int)
    consultas: list[str] = []
    for s in sementes:
        consultas.append(s)
        consultas.append(s + " ")
        if expandir:
            consultas.extend(f"{s} {letra}" for letra in string.ascii_lowercase)
    total = len(consultas)
    for i, q in enumerate(consultas, 1):
        print(f"\r  YouTube: consultando sugestões {i}/{total}...", end="", flush=True)
        for pos, sug in enumerate(sugestoes_youtube(q)):
            sug = sug.strip().lower()
            if sug in {s.lower() for s in sementes}:
                continue
            pontos[sug] += max(1, 10 - pos)
        time.sleep(0.15)
    print()
    return sorted(pontos.items(), key=lambda kv: kv[1], reverse=True)


def coletar_google_trends(termo: str, periodo: str = "now 7-d", pais: str = "BR") -> dict:
    """Retorna buscas em alta, buscas principais e a variação de interesse.

    O Google Trends às vezes bloqueia por excesso de acessos (erro 429). Nesse caso
    a função devolve só o aviso e o relatório segue com os dados do YouTube.
    """
    resultado: dict = {"em_alta": [], "principais": [], "variacao": None, "erro": None}
    try:
        from pytrends.request import TrendReq

        print("  Google Trends: consultando...")
        tr = TrendReq(hl="pt-BR", tz=180, timeout=(10, 25))
        tr.build_payload([termo], timeframe=periodo, geo=pais)

        relacionadas = tr.related_queries().get(termo) or {}
        em_alta = relacionadas.get("rising")
        principais = relacionadas.get("top")
        if em_alta is not None and not em_alta.empty:
            resultado["em_alta"] = [
                (str(l["query"]), str(l["value"])) for _, l in em_alta.head(15).iterrows()
            ]
        if principais is not None and not principais.empty:
            resultado["principais"] = [
                (str(l["query"]), int(l["value"])) for _, l in principais.head(15).iterrows()
            ]

        serie = tr.interest_over_time()
        if serie is not None and not serie.empty and termo in serie:
            valores = serie[termo].tolist()
            meio = len(valores) // 2
            antes = sum(valores[:meio]) / max(1, meio)
            depois = sum(valores[meio:]) / max(1, len(valores) - meio)
            if antes > 0:
                resultado["variacao"] = round((depois - antes) / antes * 100)
    except Exception as exc:
        resultado["erro"] = str(exc)[:200]
    return resultado


def gerar_relatorio(sementes: list[str] | None = None, rapido: bool = False) -> str:
    sementes = sementes or ["gta 6", "gta vi"]
    hoje = dt.date.today().isoformat()
    print("Caçando tendências de GTA 6...")

    trends = coletar_google_trends("GTA 6")
    yt = coletar_youtube(sementes, expandir=not rapido)

    linhas = [f"# Tendências de GTA 6 — {hoje}", ""]

    linhas.append("## Google Trends (Brasil, últimos 7 dias)")
    if trends["erro"]:
        linhas.append(
            "_O Google Trends recusou a consulta agora (é comum, tente mais tarde). "
            f"Detalhe: {trends['erro']}_"
        )
    else:
        if trends["variacao"] is not None:
            sinal = "+" if trends["variacao"] >= 0 else ""
            linhas.append(
                f"Interesse em \"GTA 6\" na segunda metade do período vs. primeira: "
                f"**{sinal}{trends['variacao']}%**"
            )
        if trends["em_alta"]:
            linhas += ["", "### Buscas em alta (crescendo rápido)"]
            for q, v in trends["em_alta"]:
                v = "explosão" if v.lower() == "breakout" else f"+{v}%"
                linhas.append(f"- {q} ({v})")
        if trends["principais"]:
            linhas += ["", "### Buscas principais"]
            for q, v in trends["principais"]:
                linhas.append(f"- {q} (índice {v})")
    linhas.append("")

    linhas.append("## O que as pessoas digitam no YouTube")
    linhas.append("_Pontuação maior = aparece mais e mais alto nas sugestões._")
    linhas.append("")
    if not yt:
        linhas.append("_O YouTube não respondeu. Verifique a internet e tente de novo._")
    for i, (q, p) in enumerate(yt[:40], 1):
        linhas.append(f"{i}. {q} — {p} pts")
    linhas.append("")
    linhas.append("## Próximo passo")
    linhas.append(
        "Escolha um tema e rode no menu a opção **2 (Roteiro)**, ou:  "
        "`python canal.py roteiro \"tema escolhido\"`"
    )

    texto = "\n".join(linhas) + "\n"
    PASTA_TENDENCIAS.mkdir(exist_ok=True)
    arquivo = PASTA_TENDENCIAS / f"{hoje}.md"
    arquivo.write_text(texto, encoding="utf-8")

    print()
    print(texto)
    print(f"Relatório salvo em: {arquivo}")
    return texto
