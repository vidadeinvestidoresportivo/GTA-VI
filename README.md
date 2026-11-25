# Canal GTA — ferramentas de produção

Quatro "agentes" gratuitos que rodam no seu PC com Windows:

| # | Agente | O que faz |
|---|--------|-----------|
| 1 | **Tendências** | Mostra o que as pessoas estão buscando sobre GTA 6 (YouTube + Google Trends) |
| 2 | **Roteiro** | Cria a pasta do vídeo e um prompt pronto para colar no Claude (claude.ai) |
| 3 | **Editor** | Junta o seu gameplay com a sua narração e gera o **Short (9:16)** e o **vídeo longo (16:9)**, com legendas automáticas |
| 4 | **Thumbnail** | Gera 5 opções de thumbnail a partir de quadros do seu gameplay |

A publicação no YouTube fica com você.

---

## 1. Instalação (uma vez só)

1. Baixe este projeto: no GitHub, clique em **Code → Download ZIP** e extraia numa pasta
   (ex.: `C:\CanalGTA`). Evite pastas dentro do OneDrive.
2. Dê dois cliques em **`instalar.bat`**.
   - Se aparecer "Python não encontrado", ele instala o Python sozinho. Feche a janela e rode o
     `instalar.bat` de novo.
   - Ele também instala o **ffmpeg** (o motor de edição de vídeo).
3. Pronto. Para usar, dê dois cliques em **`iniciar.bat`**. Vai abrir este menu:

```
================ CANAL GTA ================
  1. Tendências  (o que está em alta sobre GTA 6)
  2. Roteiro     (cria projeto + prompt para o Claude)
  3. Editar      (gameplay + sua voz -> Short e vídeo longo)
  4. Thumbnail   (gera opções de thumbnail)
  0. Sair
```

> Na primeira vez que você editar um vídeo, o programa baixa o modelo de legendas (Whisper,
> ~500 MB). Depois ele fica salvo e funciona até sem internet.

---

## 2. Fluxo de um vídeo

### Passo 1: escolher o assunto
Menu **1**. O relatório aparece na tela e fica salvo em `tendencias\AAAA-MM-DD.md`.
Os temas do topo são os mais buscados.

### Passo 2: roteiro
Menu **2**, digite o tema (ex.: *Tudo sobre o mapa de GTA 6*) e escolha `ambos`.

- Ele cria a pasta `projetos\2026-11-25-tudo-sobre-o-mapa-de-gta-6\`.
- O prompt já fica **copiado**: abra o [claude.ai](https://claude.ai), cole com **Ctrl+V** e envie.
- O Claude devolve o **roteiro**, as **cenas para gravar**, **5 títulos**, o **texto da thumbnail**,
  a **descrição** e as **tags**.
- O prompt do vídeo longo está no arquivo `prompt_roteiro_longo.txt` dentro da pasta.

### Passo 3: gravar
- **Gameplay:** grave as cenas sugeridas (Xbox/PS: compartilhar clipe; PC: OBS ou Xbox Game Bar
  com **Win+Alt+R**).
- **Narração:** leia o roteiro no celular ou no PC. Dicas: fale perto do microfone, num cômodo
  com cortinas ou roupas (menos eco) e deixe 1 segundo de silêncio no começo.

Coloque tudo na pasta do projeto:

| Arquivo | O que é |
|---------|---------|
| `gameplay.mp4` | seu vídeo do jogo (qualquer nome; .mp4, .mkv, .mov). Vários arquivos são emendados em ordem alfabética |
| `narracao_short.mp3` | sua voz para o Short (.mp3, .wav, .m4a...) |
| `narracao_longo.mp3` | sua voz para o vídeo longo |
| `narracao.mp3` | se tiver um áudio só, ele vale para os dois |

### Passo 4: editar
Menu **3**, escolha o projeto e responda as perguntas (pode só apertar Enter para usar o padrão).

- **Estilo do Short:**
  - `corte`: o jogo ocupa a tela toda (corta as laterais).
  - `desfocado`: mostra o jogo inteiro no meio, com o próprio jogo borrado no fundo.
- **Começar em qual segundo:** para pular o começo do gameplay (menus, loading).
- **Volume do jogo:** `0.15` deixa o som do jogo baixinho por baixo da sua voz. `0` tira o som.

Os vídeos prontos aparecem em `saida\`:
- `..._short.mp4`: vertical, até 60s, com legendas grandes (a palavra falada fica amarela).
- `..._longo.mp4`: horizontal 1920x1080.
- `..._longo.srt`: legenda para enviar no YouTube Studio (aba **Legendas → Enviar arquivo**).
  Isso ajuda o vídeo a aparecer nas buscas.

O áudio sai normalizado no volume que o YouTube usa (-14 LUFS).

### Passo 5: thumbnail
Menu **4**, escolha o projeto e digite o texto (2 a 4 palavras, o Claude sugere).
São geradas 5 opções em `saida\thumb_1.jpg` até `thumb_5.jpg`. Escolha a melhor.

### Passo 6: publicar
No YouTube Studio: envie o vídeo, cole título, descrição e tags do Claude, envie a thumbnail
e o `.srt`.

---

## Uso pelo terminal (opcional)

Na pasta do projeto, com o ambiente ativado (`.venv\Scripts\activate`):

```bat
python canal.py tendencias
python canal.py tendencias "gta 6 online" "gta 6 pc"
python canal.py roteiro "Mapa de GTA 6" --formato ambos
python canal.py editar mapa --formato short --estilo desfocado --inicio-short 12
python canal.py thumb mapa --texto "MAPA GIGANTE" --lado direita
python canal.py thumb mapa --texto "VAZOU TUDO" --imagem C:\Users\voce\Desktop\print.png
```

Opções úteis do `editar`:
- `--modelo tiny|base|small|medium`: qualidade das legendas. `small` é o padrão;
  `medium` acerta mais, mas é mais lento.
- `--fps 30`: renderiza mais rápido (o padrão é 60).
- `--sem-legenda`: Short sem legendas.

---

## Cuidados para o canal crescer sem problemas

- **Use só o seu gameplay.** Trechos de outros canais ou trailers inteiros geram strike.
  Pedaços curtos de trailer **comentados por você** costumam ser aceitos, mas sempre há risco.
- **Rumor é rumor.** O prompt pede para o Claude separar o que é confirmado do que é vazamento.
  Mantenha isso no vídeo: credibilidade vale mais que um clique.
- **Revise o roteiro.** O Claude pode não saber de novidades muito recentes sobre GTA 6.
  Confira datas e fatos antes de gravar.

---

## Problemas comuns

| Problema | Solução |
|----------|---------|
| "ffmpeg não encontrado" | Rode o `instalar.bat` de novo, feche e reabra o `iniciar.bat` |
| Google Trends "recusou a consulta" | Normal, ele limita acessos. Tente mais tarde; os dados do YouTube aparecem mesmo assim |
| Legendas com palavras erradas | Use `--modelo medium`, ou grave com menos ruído de fundo |
| Edição muito lenta | Use `--fps 30`, ou gere só um formato por vez |
| Acentos estranhos na janela preta | Pode ignorar; os arquivos ficam corretos |
