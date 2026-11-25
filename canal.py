"""Canal GTA — central de comando.

Sem argumentos abre um menu. Também dá para usar direto:
  python canal.py tendencias
  python canal.py roteiro "Mapa de GTA 6" --formato ambos
  python canal.py editar 2026-11-25-mapa-de-gta-6
  python canal.py thumb 2026-11-25-mapa-de-gta-6 --texto "MAPA GIGANTE"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass

from agentes.util import ErroCanal, abrir_pasta, listar_projetos, resolver_projeto


# ----------------------------------------------------------------- comandos

def cmd_tendencias(a) -> None:
    from agentes import tendencias

    sementes = a.termos or None
    tendencias.gerar_relatorio(sementes, rapido=a.rapido)


def cmd_roteiro(a) -> None:
    from agentes import roteiro

    roteiro.criar_projeto(a.tema, a.formato, a.contexto or "")


def cmd_editar(a) -> None:
    from agentes import editor

    pasta = resolver_projeto(a.projeto)
    op = editor.OpcoesEdicao(
        formatos=("short", "longo") if a.formato == "ambos" else (a.formato,),
        estilo_short=a.estilo,
        volume_jogo=a.volume_jogo,
        inicio_short=a.inicio_short,
        inicio_longo=a.inicio_longo,
        max_short=a.max_short,
        legenda_short=not a.sem_legenda,
        modelo_whisper=a.modelo,
        fps=a.fps,
    )
    editor.editar(pasta, op)
    abrir_pasta(pasta / "saida")


def cmd_thumb(a) -> None:
    from agentes import thumbnail

    pasta = resolver_projeto(a.projeto)
    thumbnail.gerar(
        pasta,
        a.texto,
        selo=None if a.sem_selo else a.selo,
        tempos=a.tempos,
        imagem=Path(a.imagem) if a.imagem else None,
        lado=a.lado,
    )
    abrir_pasta(pasta / "saida")


# ----------------------------------------------------------------- menu

def perguntar(texto: str, padrao: str = "") -> str:
    sufixo = f" [{padrao}]" if padrao else ""
    resp = input(f"{texto}{sufixo}: ").strip()
    return resp or padrao


def escolher_projeto() -> str:
    projetos = listar_projetos()
    if not projetos:
        raise ErroCanal("Nenhum projeto ainda. Use a opção 2 (Roteiro) para criar um.")
    print("\nProjetos (mais recentes primeiro):")
    for i, p in enumerate(projetos[:15], 1):
        print(f"  {i}. {p.name}")
    n = perguntar("Número do projeto", "1")
    try:
        return str(projetos[int(n) - 1])
    except (ValueError, IndexError):
        raise ErroCanal("Número inválido.")


def menu(parser: argparse.ArgumentParser) -> None:
    while True:
        print(
            "\n================ CANAL GTA ================\n"
            "  1. Tendências  (o que está em alta sobre GTA 6)\n"
            "  2. Roteiro     (cria projeto + prompt para o Claude)\n"
            "  3. Editar      (gameplay + sua voz -> Short e vídeo longo)\n"
            "  4. Thumbnail   (gera opções de thumbnail)\n"
            "  0. Sair\n"
            "==========================================="
        )
        op = input("Escolha: ").strip()
        try:
            if op == "1":
                cmd_tendencias(parser.parse_args(["tendencias"]))
            elif op == "2":
                tema = perguntar("Tema do vídeo (ex.: Tudo sobre o mapa de GTA 6)")
                if not tema:
                    continue
                formato = perguntar("Formato: short, longo ou ambos", "ambos")
                cmd_roteiro(parser.parse_args(["roteiro", tema, "--formato", formato]))
            elif op == "3":
                projeto = escolher_projeto()
                formato = perguntar("Gerar: short, longo ou ambos", "ambos")
                args = ["editar", projeto, "--formato", formato]
                if formato in ("short", "ambos"):
                    estilo = perguntar("Estilo do Short: corte (tela cheia) ou desfocado (jogo inteiro)", "corte")
                    inicio = perguntar("Começar o Short em qual segundo do gameplay", "0")
                    args += ["--estilo", estilo, "--inicio-short", inicio]
                if formato in ("longo", "ambos"):
                    args += ["--inicio-longo", perguntar("Começar o vídeo longo em qual segundo", "0")]
                args += ["--volume-jogo", perguntar("Volume do som do jogo (0 a 1)", "0.15")]
                cmd_editar(parser.parse_args(args))
            elif op == "4":
                projeto = escolher_projeto()
                texto = perguntar("Texto da thumbnail (2 a 4 palavras)")
                if not texto:
                    continue
                cmd_thumb(parser.parse_args(["thumb", projeto, "--texto", texto]))
            elif op == "0":
                return
        except ErroCanal as e:
            print(f"\n[!] {e}")
        except ModuleNotFoundError as e:
            print(f"\n[!] Biblioteca faltando: {e.name}. Feche e abra o iniciar.bat de novo "
                  "(ele instala o que falta).")
        except KeyboardInterrupt:
            print("\nCancelado.")


# ----------------------------------------------------------------- main

def criar_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Ferramentas do canal de GTA")
    sub = p.add_subparsers(dest="comando")

    t = sub.add_parser("tendencias", help="Assuntos de GTA 6 em alta")
    t.add_argument("termos", nargs="*", help="Termos base (padrão: 'gta 6' e 'gta vi')")
    t.add_argument("--rapido", action="store_true", help="Menos consultas, mais rápido")
    t.set_defaults(func=cmd_tendencias)

    r = sub.add_parser("roteiro", help="Cria projeto e prompt de roteiro")
    r.add_argument("tema")
    r.add_argument("--formato", choices=["short", "longo", "ambos"], default="ambos")
    r.add_argument("--contexto", help="Informações/fontes que o roteiro deve usar")
    r.set_defaults(func=cmd_roteiro)

    e = sub.add_parser("editar", help="Gera os vídeos a partir do gameplay e da narração")
    e.add_argument("projeto", help="Nome (ou parte do nome) da pasta do projeto")
    e.add_argument("--formato", choices=["short", "longo", "ambos"], default="ambos")
    e.add_argument("--estilo", choices=["corte", "desfocado"], default="corte")
    e.add_argument("--volume-jogo", type=float, default=0.15)
    e.add_argument("--inicio-short", type=float, default=0.0)
    e.add_argument("--inicio-longo", type=float, default=0.0)
    e.add_argument("--max-short", type=float, default=60.0)
    e.add_argument("--sem-legenda", action="store_true")
    e.add_argument("--modelo", default="small", help="Modelo Whisper: tiny, base, small, medium")
    e.add_argument("--fps", type=int, default=60)
    e.set_defaults(func=cmd_editar)

    th = sub.add_parser("thumb", help="Gera thumbnails")
    th.add_argument("projeto")
    th.add_argument("--texto", required=True)
    th.add_argument("--selo", default="GTA 6")
    th.add_argument("--sem-selo", action="store_true")
    th.add_argument("--tempos", type=float, nargs="*", help="Segundos do gameplay para usar")
    th.add_argument("--imagem", help="Usar uma imagem sua em vez de um quadro do gameplay")
    th.add_argument("--lado", choices=["esquerda", "direita"], default="esquerda")
    th.set_defaults(func=cmd_thumb)
    return p


def main() -> None:
    parser = criar_parser()
    if len(sys.argv) == 1:
        menu(parser)
        return
    a = parser.parse_args()
    if not getattr(a, "func", None):
        parser.print_help()
        return
    try:
        a.func(a)
    except ErroCanal as e:
        print(f"\n[!] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
