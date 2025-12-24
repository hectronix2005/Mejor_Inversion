"""
Orquestador de scrapers - Ejecuta y coordina todos los scrapers
"""
import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .config import BANKS_CONFIG, DATA_DIR, RATES_FILE, HISTORY_DIR
from .bank_scrapers import get_scraper, SCRAPERS
from .base_scraper import ScrapingResult, CDTRate

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CDTOrchestrator:
    """Orquesta la ejecucion de todos los scrapers"""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.results: Dict[str, ScrapingResult] = {}
        self._ensure_directories()

    def _ensure_directories(self):
        """Crea los directorios necesarios si no existen"""
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(HISTORY_DIR, exist_ok=True)

    def scrape_bank(self, bank_code: str) -> Optional[ScrapingResult]:
        """Ejecuta el scraper para un banco especifico"""
        scraper = get_scraper(bank_code)
        if not scraper:
            logger.warning(f"No se encontro scraper para {bank_code}")
            return None

        result = scraper.run()
        self.results[bank_code] = result
        return result

    def scrape_all(self, parallel: bool = True) -> Dict[str, ScrapingResult]:
        """Ejecuta todos los scrapers disponibles"""
        bank_codes = list(SCRAPERS.keys())

        if parallel:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self.scrape_bank, code): code
                    for code in bank_codes
                }

                for future in as_completed(futures):
                    bank_code = futures[future]
                    try:
                        result = future.result()
                        if result:
                            logger.info(f"{bank_code}: {len(result.rates)} tasas")
                    except Exception as e:
                        logger.error(f"Error en {bank_code}: {e}")
        else:
            for code in bank_codes:
                result = self.scrape_bank(code)
                if result:
                    logger.info(f"{code}: {len(result.rates)} tasas")
                time.sleep(1)  # Rate limiting

        return self.results

    def get_all_rates(self) -> List[Dict]:
        """Obtiene todas las tasas de todos los bancos"""
        all_rates = []
        for result in self.results.values():
            if result.success:
                all_rates.extend([r.to_dict() for r in result.rates])
        return all_rates

    def get_rates_by_term(self, term_days: int) -> List[Dict]:
        """Obtiene tasas filtradas por plazo"""
        all_rates = self.get_all_rates()
        return [r for r in all_rates if r['term_days'] == term_days]

    def get_best_rates(self, term_days: Optional[int] = None, top_n: int = 10) -> List[Dict]:
        """Obtiene las mejores tasas, opcionalmente filtradas por plazo"""
        if term_days:
            rates = self.get_rates_by_term(term_days)
        else:
            rates = self.get_all_rates()

        # Ordenar por tasa descendente
        rates.sort(key=lambda x: x['rate_ea'], reverse=True)
        return rates[:top_n]

    def get_ranking(self) -> Dict:
        """Genera el ranking completo de CDTs"""
        all_rates = self.get_all_rates()

        # Ranking general
        all_rates.sort(key=lambda x: x['rate_ea'], reverse=True)

        # Rankings por plazo
        rankings_by_term = {}
        for term in [30, 60, 90, 180, 360, 540, 720]:
            term_rates = [r for r in all_rates if r['term_days'] == term]
            term_rates.sort(key=lambda x: x['rate_ea'], reverse=True)
            rankings_by_term[term] = term_rates

        # Estadisticas
        if all_rates:
            avg_rate = sum(r['rate_ea'] for r in all_rates) / len(all_rates)
            max_rate = max(r['rate_ea'] for r in all_rates)
            min_rate = min(r['rate_ea'] for r in all_rates)
        else:
            avg_rate = max_rate = min_rate = 0

        return {
            'generated_at': datetime.now().isoformat(),
            'total_banks': len([r for r in self.results.values() if r.success]),
            'total_rates': len(all_rates),
            'statistics': {
                'average_rate': round(avg_rate, 2),
                'max_rate': round(max_rate, 2),
                'min_rate': round(min_rate, 2)
            },
            'top_10': all_rates[:10],
            'by_term': rankings_by_term,
            'all_rates': all_rates
        }

    def save_results(self):
        """Guarda los resultados en archivos JSON"""
        ranking = self.get_ranking()

        # Guardar ranking actual
        with open(RATES_FILE, 'w', encoding='utf-8') as f:
            json.dump(ranking, f, ensure_ascii=False, indent=2)
        logger.info(f"Ranking guardado en {RATES_FILE}")

        # Guardar historial
        history_file = os.path.join(
            HISTORY_DIR,
            f"rates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(ranking, f, ensure_ascii=False, indent=2)
        logger.info(f"Historial guardado en {history_file}")

        return ranking

    def load_cached_results(self) -> Optional[Dict]:
        """Carga resultados cacheados si existen"""
        if os.path.exists(RATES_FILE):
            try:
                with open(RATES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return None
        return None


def run_scraping() -> Dict:
    """Funcion principal para ejecutar el scraping completo"""
    logger.info("Iniciando scraping de CDTs...")
    start_time = time.time()

    orchestrator = CDTOrchestrator(max_workers=5)
    orchestrator.scrape_all(parallel=True)
    ranking = orchestrator.save_results()

    duration = time.time() - start_time
    logger.info(f"Scraping completado en {duration:.2f} segundos")
    logger.info(f"Total bancos: {ranking['total_banks']}")
    logger.info(f"Total tasas: {ranking['total_rates']}")

    return ranking


if __name__ == '__main__':
    run_scraping()
