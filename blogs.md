# Incorporação de blogs e feeds ao indexador

## Objetivo

Adicionar ao projeto uma nova camada de coleta de conteúdo baseada em **blogs, feeds RSS/Atom, changelogs e blogs de engenharia**, priorizando fontes estáveis e densas em informação técnica.

A proposta é **não usar X/Twitter**. Em vez disso, o indexador deve consumir fontes mais robustas, com menor ruído e maior confiabilidade.

---

## Diretriz geral

Implementar uma nova etapa chamada `blog_sources` ou equivalente, com estas características:

1. Ler um catálogo de fontes em YAML.
2. Coletar itens via RSS/Atom quando disponível.
3. Quando o feed não estiver disponível explicitamente, tentar autodiscovery do feed a partir do HTML.
4. Normalizar todos os itens para um schema comum.
5. Deduplicar por URL canônica + hash de título.
6. Classificar por tema.
7. Resumir apenas os itens mais relevantes.
8. Entregar isso junto do relatório diário/semanal já existente.

---

## Estrutura sugerida de pastas

```text
indexador/
  config/
    sources.yaml
  src/
    collectors/
      rss_collector.py
      blog_discovery.py
    processors/
      normalize_posts.py
      rank_posts.py
      deduplicate.py
      classify_posts.py
    reports/
      render_digest.py
  data/
    raw/
    processed/
  tests/
```

---

## Schema padronizado esperado

Cada item coletado deve ser normalizado para algo próximo disto:

```json
{
  "source_name": "Simon Willison",
  "source_type": "rss",
  "category": "software_dev",
  "title": "Example post",
  "author": "Simon Willison",
  "published_at": "2026-04-13T18:30:00Z",
  "url": "https://example.com/post",
  "summary": "Resumo bruto do feed ou trecho extraído",
  "content": "conteúdo textual extraído quando disponível",
  "language": "en",
  "tags": ["llm", "python"],
  "score": 0.0,
  "hash": "..."
}
```

---

## Catálogo inicial de fontes

Criar `config/sources.yaml` com algo nesta linha:

```yaml
sources:
  - name: Simon Willison
    category: software_dev
    kind: rss
    site_url: https://simonwillison.net/
    feed_url: https://simonwillison.net/atom/everything/
    language: en
    priority: 10

  - name: Martin Fowler
    category: software_architecture
    kind: rss
    site_url: https://martinfowler.com/
    feed_url: https://martinfowler.com/feed.atom
    language: en
    priority: 10

  - name: GitHub Blog
    category: software_dev
    kind: rss
    site_url: https://github.blog/
    feed_url: https://github.blog/feed/
    language: en
    priority: 9

  - name: Posit Blog
    category: data_science
    kind: rss
    site_url: https://posit.co/blog/
    feed_url: https://posit.co/blog/index.xml
    language: en
    priority: 10

  - name: DuckDB Blog
    category: data_engineering
    kind: rss
    site_url: https://duckdb.org/
    feed_url: https://duckdb.org/feed.xml
    language: en
    priority: 10

  - name: Hugging Face Blog
    category: ai_ml
    kind: rss
    site_url: https://huggingface.co/blog
    feed_url: https://huggingface.co/blog/feed.xml
    language: en
    priority: 9

  - name: Python Software Foundation Blog
    category: software_dev
    kind: rss
    site_url: https://pyfound.blogspot.com/
    feed_url: https://pyfound.blogspot.com/feeds/posts/default?alt=rss
    language: en
    priority: 8

  - name: Cloudflare Blog
    category: software_infra
    kind: rss
    site_url: https://blog.cloudflare.com/
    feed_url: https://blog.cloudflare.com/rss/
    language: en
    priority: 8

  - name: Netflix Tech Blog
    category: software_infra
    kind: rss
    site_url: https://netflixtechblog.com/
    feed_url: https://netflixtechblog.com/feed
    language: en
    priority: 7

  - name: Thoughtworks Insights
    category: software_architecture
    kind: rss
    site_url: https://www.thoughtworks.com/insights
    feed_url: https://www.thoughtworks.com/rss-insights.xml
    language: en
    priority: 7
```

---

## Regras de coleta

### 1. Leitura do catálogo

Implementar leitura de `config/sources.yaml`.

Cada fonte deve permitir:
- habilitar/desabilitar
- prioridade
- categoria
- idioma
- limite de itens por execução

Exemplo:

```yaml
settings:
  max_items_per_source: 10
  max_items_total: 80
  lookback_days: 7
```

### 2. Coleta RSS/Atom

Criar `src/collectors/rss_collector.py`.

Requisitos:
- usar `feedparser`
- timeout de requisição
- user-agent explícito
- tratamento de erro por fonte
- não interromper o pipeline inteiro se uma fonte falhar
- guardar logs por fonte

### 3. Descoberta automática de feed

Criar `src/collectors/blog_discovery.py`.

Fluxo:
- se `feed_url` existir, usar diretamente
- se não existir, baixar `site_url`
- procurar `<link rel="alternate" type="application/rss+xml">` ou atom
- persistir resultado em cache local

### 4. Extração complementar de conteúdo

Quando o feed trouxer só resumo curto:
- baixar a página do post
- extrair conteúdo legível com `trafilatura` ou `readability-lxml`
- limpar HTML e normalizar whitespace

---

## Regras de qualidade

### Deduplicação

Criar `src/processors/deduplicate.py`.

Deduplicar por:
1. URL canônica
2. título normalizado
3. hash do conteúdo limpo

### Ranking

Criar `src/processors/rank_posts.py`.

Critérios sugeridos para score:
- prioridade da fonte
- recência
- presença de palavras-chave relevantes ao projeto
- densidade técnica
- tamanho mínimo do conteúdo
- penalidade para posts muito promocionais

Exemplo de palavras-chave iniciais:
- python
- r
- duckdb
- llm
- rag
- openai
- data engineering
- analytics
- parquet
- api
- shiny
- django
- airflow
- orchestration

### Classificação temática

Criar `src/processors/classify_posts.py`.

Taxonomia inicial:
- software_dev
- software_architecture
- software_infra
- data_engineering
- data_science
- ai_ml
- product_updates

Pode começar com regras por palavras-chave e depois evoluir para classificação com LLM.

---

## Regras de resumo

Resumir apenas os itens melhor ranqueados.

Formato sugerido por item:

```markdown
### Título do post
Fonte: DuckDB Blog  
Data: 2026-04-13  
Link: https://...  

Resumo em 3 a 5 linhas, destacando:
- o que mudou
- por que importa
- possível impacto para software/dados
```

Também gerar uma seção agregada:

```markdown
## Principais sinais do período
- Novo recurso ou biblioteca relevante
- Mudança importante em ferramenta de dados
- Artigo com implicação prática para engenharia
```

---

## Regras de saída

Incluir no relatório final uma seção chamada:

- `Blogs e engenharia`
ou
- `Fontes técnicas monitoradas`

Ordenar por:
1. score desc
2. published_at desc

Limitar a saída final para evitar excesso de ruído.

Sugestão:
- até 12 itens no relatório diário
- até 25 itens no relatório semanal

---

## Dependências sugeridas

Adicionar ao projeto:

```txt
feedparser
httpx
pyyaml
trafilatura
python-dateutil
beautifulsoup4
lxml
```

Se já existir stack semelhante, reutilizar o padrão do projeto.

---

## Comportamento esperado do pipeline

Implementar algo como:

```python
sources = load_sources("config/sources.yaml")
entries = collect_all_sources(sources)
entries = normalize_entries(entries)
entries = deduplicate_entries(entries)
entries = classify_entries(entries)
entries = rank_entries(entries)
top_entries = select_top_entries(entries)
report = render_report(top_entries)
```

---

## Requisitos de robustez

- uma fonte com erro não pode derrubar a execução total
- registrar falhas por fonte
- registrar quantidade de itens coletados por fonte
- registrar quantidade de itens deduplicados
- respeitar timeout e retry simples
- salvar bruto e processado para auditoria

---

## Critérios de aceite

O trabalho será considerado concluído quando:

1. o projeto conseguir ler `config/sources.yaml`
2. coletar posts de múltiplos feeds RSS/Atom
3. normalizar tudo para um formato único
4. deduplicar resultados
5. ranquear por relevância
6. gerar uma seção nova no relatório
7. executar sem quebrar se uma ou mais fontes falharem
8. permitir expansão fácil do catálogo de fontes

---

## Melhorias futuras

Depois da primeira versão, considerar:

1. suporte a newsletters convertidas para RSS
2. suporte a changelogs e release feeds
3. detecção automática de idioma
4. embeddings para deduplicação semântica
5. clusterização por assunto
6. personalização por perfil de interesse
7. painel simples para habilitar/desabilitar fontes

---

## Observação importante

Dar preferência a **fontes primárias e técnicas**. Evitar sites muito genéricos, agregadores excessivamente promocionais ou conteúdo de baixa densidade técnica.

A intenção do indexador deve ser produzir um resumo útil para alguém que acompanha:
- desenvolvimento de software
- análise de dados
- engenharia de dados
- IA aplicada
- ferramentas como Python, R, DuckDB, Shiny, APIs e infraestrutura de automação

---

## Notas para implementação

- Se o projeto já possuir estrutura de jobs, encaixar essa coleta como mais uma etapa do pipeline existente.
- Se já houver banco local ou storage intermediário, persistir os itens coletados lá.
- Se já houver rotina de envio por e-mail ou WhatsApp, apenas incorporar a nova seção ao payload final.
- Manter o código modular para que novas fontes sejam adicionadas apenas via YAML.

