#!/usr/bin/env python3
"""
Script principal para ejecutar el sistema de comparacion de CDTs
"""
import os
import sys
import argparse
import logging

# Agregar el directorio raiz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_scraper():
    """Ejecuta el scraping de todos los bancos"""
    from scrapers.orchestrator import run_scraping
    logger.info("Iniciando scraping de CDTs...")
    result = run_scraping()
    logger.info(f"Scraping completado: {result['total_rates']} tasas de {result['total_banks']} bancos")
    return result


def run_api(host='0.0.0.0', port=5001, debug=True):
    """Ejecuta el servidor API"""
    from api.app import app, run_scraping
    from scrapers.config import RATES_FILE

    # Verificar si hay datos, si no ejecutar scraping
    if not os.path.exists(RATES_FILE):
        logger.info("No hay datos. Ejecutando scraping inicial...")
        run_scraping()

    logger.info(f"Iniciando servidor API en http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


def run_all():
    """Ejecuta scraping y luego inicia el servidor"""
    run_scraper()
    run_api()


def show_rates():
    """Muestra las tasas actuales"""
    import json
    from scrapers.config import RATES_FILE

    if not os.path.exists(RATES_FILE):
        logger.error("No hay datos. Ejecuta primero: python run.py scrape")
        return

    with open(RATES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("\n" + "="*60)
    print("RANKING DE CDTs - MEJORES TASAS")
    print("="*60)
    print(f"Generado: {data['generated_at']}")
    print(f"Total bancos: {data['total_banks']}")
    print(f"Total tasas: {data['total_rates']}")
    print(f"\nEstadisticas:")
    print(f"  - Tasa promedio: {data['statistics']['average_rate']:.2f}%")
    print(f"  - Tasa maxima: {data['statistics']['max_rate']:.2f}%")
    print(f"  - Tasa minima: {data['statistics']['min_rate']:.2f}%")

    print("\n" + "-"*60)
    print("TOP 10 MEJORES TASAS:")
    print("-"*60)
    for i, rate in enumerate(data['top_10'][:10], 1):
        print(f"{i:2}. {rate['bank_name']:20} | {rate['term_days']:4} dias | {rate['rate_ea']:.2f}% E.A.")

    print("\n" + "-"*60)
    print("MEJORES TASAS POR PLAZO (360 dias):")
    print("-"*60)
    for rate in data['by_term'].get('360', [])[:5]:
        print(f"   {rate['bank_name']:20} | {rate['rate_ea']:.2f}% E.A.")

    print("="*60 + "\n")


def run_verify(bank_code: str = None):
    """Ejecuta verificacion de URLs"""
    from scrapers.url_verifier import URLVerifier, generate_report, save_report, BANK_URLS

    verifier = URLVerifier()

    if bank_code:
        if bank_code not in BANK_URLS:
            logger.error(f"Banco '{bank_code}' no encontrado")
            logger.info(f"Bancos disponibles: {', '.join(BANK_URLS.keys())}")
            return
        logger.info(f"Verificando URLs de {bank_code}...")
        results = {bank_code: verifier.verify_bank(bank_code)}
    else:
        logger.info("Verificando URLs de todos los bancos...")
        results = verifier.verify_all_banks(parallel=True)

    # Mostrar reporte
    print(generate_report(results, 'text'))

    # Guardar reportes
    json_path, txt_path = save_report(results)
    logger.info(f"Reportes guardados: {txt_path}")

    return results


def list_banks():
    """Lista todos los bancos disponibles"""
    from scrapers.url_verifier import BANK_URLS

    print("\n" + "=" * 60)
    print("BANCOS DISPONIBLES")
    print("=" * 60)

    for code, info in sorted(BANK_URLS.items()):
        print(f"\n{info['name']} ({code})")
        print(f"  URL: {info['main_url']}")
        print(f"  Notas: {info.get('notes', 'N/A')}")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Sistema de Comparacion de CDTs Colombia'
    )
    parser.add_argument(
        'command',
        choices=['scrape', 'api', 'all', 'show', 'verify', 'list', 'review'],
        help='Comando: scrape, api, all, show, verify, list, review (abrir revision manual)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host para el servidor API (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5001,
        help='Puerto para el servidor API (default: 5001)'
    )
    parser.add_argument(
        '--no-debug',
        action='store_true',
        help='Desactivar modo debug'
    )
    parser.add_argument(
        '--bank', '-b',
        help='Codigo del banco (para comando verify)'
    )

    args = parser.parse_args()

    if args.command == 'scrape':
        run_scraper()
    elif args.command == 'api':
        run_api(host=args.host, port=args.port, debug=not args.no_debug)
    elif args.command == 'all':
        run_all()
    elif args.command == 'show':
        show_rates()
    elif args.command == 'verify':
        run_verify(bank_code=args.bank)
    elif args.command == 'list':
        list_banks()
    elif args.command == 'review':
        from scrapers.manual_review import open_review_page
        open_review_page()


if __name__ == '__main__':
    main()
