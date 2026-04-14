# Tech Radar

Projeto Python para coletar noticias via RSS/Atom, filtrar conteudos relevantes, classificar por tema, gerar um relatorio HTML responsivo e enviar por e-mail.
Agora o projeto tambem suporta um catalogo em YAML para monitorar blogs de engenharia, changelogs e fontes tecnicas com autodiscovery de feed.

## Recomendacao de ambiente

O melhor fluxo para este projeto e usar WSL com Ubuntu, porque ele fica mais proximo do servidor final:

- mesmo estilo de path Linux
- mesma chamada com `python3`
- uso natural de `cron`
- menos diferencas entre desenvolvimento e execucao no servidor

Se estiver no Windows, prefira manter o projeto dentro do filesystem do Linux do WSL, por exemplo:

```bash
~/projects/tech_radar
```

Evite trabalhar em `/mnt/c/...` se a ideia for desenvolver e testar no WSL.

## Requisitos

- Python 3.11+
- Ubuntu ou WSL com Ubuntu
- Acesso SMTP para envio de e-mail

## Estrutura

```text
tech_radar/
├── app.py
├── blog_sources.py
├── config.py
├── config/
│   └── sources.yaml
├── feeds.py
├── filters.py
├── classifier.py
├── report.py
├── mailer.py
├── utils.py
├── requirements.txt
├── .env.example
├── README.md
├── logs/
└── data/
```

## Setup recomendado no WSL

### 1. Mover o projeto para o Linux do WSL

```bash
mkdir -p ~/projects
cp -r /mnt/c/Users/jpwah/OneDrive/Projetos/indexador/tech_radar ~/projects/
cd ~/projects/tech_radar
```

### 2. Instalar Python e suporte a venv

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### 3. Criar ambiente virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configurar variaveis de ambiente

```bash
cp .env.example .env
nano .env
```

Exemplo:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=meuemail@gmail.com
SMTP_PASS=sua_senha_ou_app_password
EMAIL_FROM=meuemail@gmail.com
EMAIL_TO=destino@gmail.com
EMAIL_SUBJECT=Radar Tech Diario
```

Se usar Gmail, prefira `App Password` em vez da senha normal da conta.

## Execucao

Rodar sem enviar e-mail:

```bash
python app.py --dry-run
```

Rodar com envio:

```bash
python app.py
```

Arquivos gerados:

- `data/latest.json`: ultima coleta em JSON
- `data/latest_report.html`: relatorio HTML mais recente
- `logs/radar.log`: log principal da aplicacao

## Cron no Ubuntu ou WSL

Abra o crontab:

```bash
crontab -e
```

Exemplo para executar todos os dias as 07:00 usando a venv:

```cron
0 7 * * * cd /home/SEU_USUARIO/projects/tech_radar && /home/SEU_USUARIO/projects/tech_radar/.venv/bin/python app.py >> /home/SEU_USUARIO/projects/tech_radar/logs/cron.log 2>&1
```

Troque `SEU_USUARIO` pelo seu usuario real.

## Como funciona

1. `feeds.py` coleta os feeds configurados em `config.py`
2. `blog_sources.py` le um catalogo YAML, descobre feeds e coleta fontes tecnicas
3. `filters.py` remove duplicados, spam e itens irrelevantes
4. `classifier.py` atribui categoria por palavras-chave
5. `report.py` gera HTML responsivo, incluindo a secao `Blogs e engenharia`
6. `mailer.py` envia o relatorio por SMTP

## Personalizacao

- Adicione feeds rapidos em `FEEDS`, no arquivo `config.py`
- Adicione blogs e fontes tecnicas em `config/sources.yaml`
- Ajuste palavras-chave em `CATEGORIES`
- Mude o limite total de noticias em `MAX_ITEMS`
- Ajuste pesos de relevancia em `RELEVANCE_KEYWORDS`
- Ajuste limites por fonte e janela de coleta em `config/sources.yaml`

## Expansao futura

O projeto ja possui ponto simples para integracoes futuras:

- IA: funcao `summarize(text)` em `classifier.py`
- WhatsApp: fluxo atual deixa o conteudo consolidado pronto para reuso em outro canal

## Observacoes

- Se um feed falhar, os demais continuam
- Se uma fonte tecnica falhar ou nao tiver feed descoberto, a execucao continua
- Se o envio do e-mail falhar, o erro fica registrado em log
- Hacker News pode retornar itens com pouco resumo; o filtro tolera isso
- O bruto das fontes tecnicas fica salvo em `data/raw/blog_sources_raw.json`
