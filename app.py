from __future__ import annotations

import argparse

from blog_sources import fetch_blog_sources
from classifier import classify_items
from config import DATA_DIR, LOG_FILE
from feeds import fetch_all_feeds
from filters import filter_items
from mailer import send_report_email
from report import build_html_report
from utils import save_json, setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Coleta noticias de tecnologia, gera relatorio HTML e envia por e-mail."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Gera o HTML localmente e nao envia e-mail.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger = setup_logging(LOG_FILE)
    logger.info("Iniciando execucao do Tech Radar")

    raw_items = fetch_all_feeds(logger)
    raw_items.extend(fetch_blog_sources(logger))
    logger.info("Total bruto de itens coletados: %s", len(raw_items))

    filtered_items = filter_items(raw_items, logger)
    classified_items = classify_items(filtered_items)

    latest_path = DATA_DIR / "latest.json"
    save_json(latest_path, classified_items, logger)

    html_report = build_html_report(classified_items)
    report_path = DATA_DIR / "latest_report.html"
    report_path.write_text(html_report, encoding="utf-8")
    logger.info("Relatorio HTML salvo em %s", report_path)

    if args.dry_run:
        logger.info("Dry-run ativo: e-mail nao sera enviado")
        print(f"Relatorio gerado em: {report_path}")
        return 0

    email_sent = send_report_email(html_report, logger)
    if not email_sent:
        logger.error("Execucao finalizada com falha no envio do e-mail")
        return 1

    logger.info("Execucao finalizada com sucesso")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
