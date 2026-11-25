"""Agente 2: roteirista (versão gratuita).

Cria a pasta do projeto e um prompt pronto. Você cola o prompt no chat do Claude
(claude.ai) e recebe o roteiro, os títulos, o texto da thumbnail, a descrição e as tags.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from .util import PASTA_PROJETOS, copiar_para_area_de_transferencia, slug

FORMATOS = {
    "short": {
        "nome": "YouTube Short (vertical, 9:16)",
        "duracao": "entre 35 e 55 segundos",
        "palavras": "entre 90 e 140 palavras",
        "estrutura": (
            "- GANCHO (0-3s): uma frase que prende na hora, sem enrolação e sem \"fala, galera\".\n"
            "- DESENVOLVIMENTO: os fatos, rápido, uma ideia por frase.\n"
            "- VIRADA/FINAL: uma informação surpreendente ou opinião forte no fim, "
            "e uma pergunta curta para gerar comentários."
        ),
    },
    "longo": {
        "nome": "vídeo longo (horizontal, 16:9)",
        "duracao": "entre 8 e 12 minutos",
        "palavras": "entre 1200 e 1800 palavras",
        "estrutura": (
            "- GANCHO (primeiros 15s): o motivo para assistir até o fim, sem rodeio.\n"
            "- PROMESSA: o que a pessoa vai saber ao final.\n"
            "- BLOCOS: de 4 a 7 tópicos, cada um com um subtítulo, e uma frase de "
            "transição que puxa para o próximo (\"mas o mais estranho vem agora...\").\n"
            "- PEDIDO DE INSCRIÇÃO: uma frase natural no meio do vídeo, não no começo.\n"
            "- FINAL: resumo em 2 frases e uma pergunta para os comentários."
        ),
    },
}

MODELO_PROMPT = """Você é roteirista de um canal brasileiro de YouTube sobre GTA 6.
Eu mesmo vou narrar com a minha voz e gravar o meu próprio gameplay.

TEMA DO VÍDEO: {tema}
FORMATO: {nome_formato}
DURAÇÃO FALADA: {duracao} ({palavras}, ritmo de fala natural)
{contexto}
ESTRUTURA:
{estrutura}

REGRAS:
- Português do Brasil falado, como um amigo explicando. Frases curtas, fáceis de ler em voz alta.
- Seja honesto: separe claramente o que é CONFIRMADO pela Rockstar do que é RUMOR ou VAZAMENTO,
  e diga a fonte quando possível. Não invente datas, números ou informações.
- Se você não tiver certeza de algo recente sobre GTA 6, me avise numa observação no final
  em vez de afirmar.
- Nada de \"fala galera, beleza?\" no início.

RESPONDA EXATAMENTE NESTAS SEÇÕES:

## ROTEIRO
(Só o texto que eu vou ler, dividido em blocos. Antes de cada bloco, entre colchetes,
o tempo aproximado e a cena de gameplay que combina, ex.: [0:00-0:03 | carro em alta
velocidade na praia].)

## CENAS PARA GRAVAR
(Lista do que eu preciso gravar no jogo para cobrir o roteiro.)

## TÍTULOS
(5 opções, até 60 caracteres, chamativas mas verdadeiras.)

## TEXTO DA THUMBNAIL
(3 opções de 2 a 4 palavras, em CAIXA ALTA.)

## DESCRIÇÃO
(3 a 5 linhas para o YouTube, com as palavras-chave principais no começo.)

## TAGS
(10 a 15 tags separadas por vírgula.)
"""


def criar_projeto(tema: str, formato: str = "ambos", contexto: str = "") -> Path:
    formatos = ["short", "longo"] if formato == "ambos" else [formato]
    pasta = PASTA_PROJETOS / f"{dt.date.today().isoformat()}-{slug(tema)}"
    pasta.mkdir(parents=True, exist_ok=True)

    bloco_contexto = f"\nINFORMAÇÕES QUE EU JÁ TENHO (use como base):\n{contexto.strip()}\n" if contexto.strip() else ""

    prompts = []
    for f in formatos:
        cfg = FORMATOS[f]
        prompt = MODELO_PROMPT.format(
            tema=tema,
            nome_formato=cfg["nome"],
            duracao=cfg["duracao"],
            palavras=cfg["palavras"],
            estrutura=cfg["estrutura"],
            contexto=bloco_contexto,
        )
        (pasta / f"prompt_roteiro_{f}.txt").write_text(prompt, encoding="utf-8")
        prompts.append((f, prompt))

    (pasta / "LEIA-ME.txt").write_text(
        LEIA_ME.format(tema=tema), encoding="utf-8"
    )

    print(f"\nProjeto criado em: {pasta}\n")
    primeiro_formato, primeiro_prompt = prompts[0]
    if copiar_para_area_de_transferencia(primeiro_prompt):
        print(f"O prompt do formato \"{primeiro_formato}\" foi COPIADO. Abra claude.ai e cole (Ctrl+V).")
    for f, _ in prompts:
        print(f"  - prompt_roteiro_{f}.txt")
    print("\nDepois siga os passos do LEIA-ME.txt dentro da pasta.")
    return pasta


LEIA_ME = """PROJETO: {tema}

PASSO A PASSO
1. Abra o arquivo prompt_roteiro_short.txt (ou _longo), copie tudo e cole no claude.ai.
2. Salve a resposta nesta pasta como roteiro.txt (opcional, mas ajuda a se organizar).
3. Grave o gameplay seguindo a seção "CENAS PARA GRAVAR".
4. Grave a sua narração lendo o ROTEIRO.
5. Coloque nesta pasta:
     gameplay.mp4            -> seu vídeo do jogo (pode ter outro nome; qualquer .mp4/.mkv/.mov)
     narracao_short.wav      -> narração do Short   (pode ser .mp3, .m4a, .wav...)
     narracao_longo.wav      -> narração do vídeo longo
   Se tiver só um áudio, pode chamar de narracao.wav: ele será usado nos dois formatos.
   Se tiver vários vídeos de gameplay, coloque todos: eles serão emendados em ordem alfabética.
6. No menu, escolha "3. Editar vídeo". Os vídeos prontos aparecem na pasta "saida".
7. No menu, escolha "4. Thumbnail" e use o texto sugerido pelo Claude.
"""
