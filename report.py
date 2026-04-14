from __future__ import annotations

from datetime import datetime
from html import escape

from classifier import group_by_category
from config import BLOG_SECTION_LIMIT, GENERAL_CATEGORY, SUMMARY_MAX_LENGTH
from utils import safe_trim


def build_html_report(items: list[dict]) -> str:
    blog_items = sorted(
        [item for item in items if item.get("collection") == "blog_sources"],
        key=lambda item: (item.get("score", 0), item.get("published_at", "")),
        reverse=True,
    )[:BLOG_SECTION_LIMIT]
    general_items = [item for item in items if item.get("collection") != "blog_sources"]
    grouped = group_by_category(general_items)
    ordered_categories = sorted(
        grouped.keys(),
        key=lambda name: (name == GENERAL_CATEGORY, name),
    )
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")

    sections = "".join(
        build_category_section(category, grouped[category]) for category in ordered_categories
    )
    blog_section = build_blog_section(blog_items)
    body_sections = f"{blog_section}{sections}"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Radar Tech</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f4f7fb;
      --panel: #ffffff;
      --text: #183046;
      --muted: #5c7285;
      --line: #d8e2ec;
      --primary: #0f6cbd;
      --accent: #19a974;
      --shadow: 0 10px 30px rgba(15, 48, 70, 0.08);
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      padding: 24px 12px;
      background:
        radial-gradient(circle at top left, rgba(25, 169, 116, 0.12), transparent 28%),
        linear-gradient(180deg, #eef4f9 0%, var(--bg) 100%);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
    }}
    .wrapper {{
      max-width: 880px;
      margin: 0 auto;
    }}
    .hero {{
      background: linear-gradient(135deg, #0f6cbd 0%, #0b4f87 55%, #083250 100%);
      color: #fff;
      border-radius: 24px;
      padding: 28px 24px;
      box-shadow: var(--shadow);
    }}
    .hero h1 {{
      margin: 0 0 8px;
      font-size: 30px;
      line-height: 1.1;
    }}
    .hero p {{
      margin: 0;
      color: rgba(255, 255, 255, 0.86);
      font-size: 15px;
    }}
    .category {{
      margin-top: 24px;
    }}
    .category-title {{
      margin: 0 0 12px;
      font-size: 20px;
      text-transform: capitalize;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
      margin-bottom: 14px;
      box-shadow: var(--shadow);
    }}
    .meta {{
      color: var(--muted);
      font-size: 13px;
      margin-bottom: 8px;
    }}
    .card a {{
      color: var(--primary);
      font-size: 18px;
      line-height: 1.3;
      text-decoration: none;
      font-weight: bold;
    }}
    .card p {{
      margin: 10px 0 0;
      font-size: 15px;
      line-height: 1.55;
      color: #28475f;
    }}
    .empty {{
      background: var(--panel);
      border-radius: 16px;
      padding: 20px;
      color: var(--muted);
      border: 1px dashed var(--line);
    }}
    .badge {{
      display: inline-block;
      margin-top: 12px;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(25, 169, 116, 0.12);
      color: var(--accent);
      font-size: 12px;
      font-weight: bold;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    @media (max-width: 600px) {{
      body {{
        padding: 16px 10px;
      }}
      .hero {{
        padding: 22px 18px;
        border-radius: 20px;
      }}
      .hero h1 {{
        font-size: 26px;
      }}
      .card {{
        padding: 16px;
        border-radius: 16px;
      }}
      .card a {{
        font-size: 17px;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <section class="hero">
      <h1>Radar Tech</h1>
      <p>Noticias filtradas sobre desenvolvimento, dados e IA.</p>
      <span class="badge">Gerado em {escape(generated_at)}</span>
    </section>
    {body_sections or '<section class="category"><div class="empty">Nenhuma noticia relevante encontrada nesta execucao.</div></section>'}
  </div>
</body>
</html>"""


def build_category_section(category: str, items: list[dict]) -> str:
    cards = "".join(build_news_card(item) for item in items)
    return f"""
    <section class="category">
      <h2 class="category-title">{escape(category)}</h2>
      {cards}
    </section>
    """


def build_news_card(item: dict) -> str:
    title = escape(item.get("title", "Sem titulo"))
    link = escape(item.get("url") or item.get("link", "#"), quote=True)
    summary = escape(safe_trim(item.get("ai_summary") or item.get("summary", ""), SUMMARY_MAX_LENGTH))
    source = escape(item.get("source_name") or item.get("source", "Fonte desconhecida"))
    published = escape(item.get("published_at") or item.get("published", ""))
    meta = " | ".join(part for part in [source, published] if part)
    return f"""
      <article class="card">
        <div class="meta">{meta}</div>
        <a href="{link}" target="_blank" rel="noopener noreferrer">{title}</a>
        <p>{summary}</p>
      </article>
    """


def build_blog_section(items: list[dict]) -> str:
    if not items:
        return ""

    cards = "".join(build_news_card(item) for item in items)
    signals = "".join(f"<li>{escape(signal)}</li>" for signal in build_blog_signals(items))
    return f"""
    <section class="category">
      <h2 class="category-title">Blogs e engenharia</h2>
      <div class="card">
        <div class="meta">Principais sinais do periodo</div>
        <ul>{signals}</ul>
      </div>
      {cards}
    </section>
    """


def build_blog_signals(items: list[dict]) -> list[str]:
    top_sources = [item.get("source_name") or item.get("source", "Fonte tecnica") for item in items[:3]]
    top_categories = [item.get("category", GENERAL_CATEGORY) for item in items[:3]]
    signals = []

    if top_sources:
        signals.append("Fontes com mais destaque: " + ", ".join(top_sources))
    if top_categories:
        signals.append("Temas tecnicos mais fortes: " + ", ".join(top_categories))
    if items:
        signals.append(f"{len(items)} posts tecnicos selecionados por relevancia e recencia.")
    return signals
