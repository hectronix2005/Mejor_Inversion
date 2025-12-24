#!/usr/bin/env python3
"""
Scraper especializado para MejorCDT.com
Fuente principal de datos consolidados de CDTs en Colombia
"""
import re
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CDTRateFromMejorCDT:
    """Tasa de CDT extraida de MejorCDT.com"""
    bank_name: str
    bank_code: str
    rate_ea: float
    term_days: int
    min_amount: Optional[float]
    max_amount: Optional[float]
    rate_type: str  # 'fijo', 'variable'
    source_url: str
    source_month: str
    scraped_at: str

    def to_dict(self) -> Dict:
        return {
            'bank_name': self.bank_name,
            'bank_code': self.bank_code,
            'rate_ea': self.rate_ea,
            'term_days': self.term_days,
            'min_amount': self.min_amount,
            'max_amount': self.max_amount,
            'rate_type': self.rate_type,
            'source_url': self.source_url,
            'source_month': self.source_month,
            'scraped_at': self.scraped_at
        }


class MejorCDTScraper:
    """
    Scraper para MejorCDT.com
    Extrae datos consolidados de tasas de CDT de todos los bancos
    """

    BASE_URL = "https://mejorcdt.com"

    # Mapeo de nombres de bancos a codigos
    BANK_CODE_MAP = {
        'bancolombia': 'bancolombia',
        'davivienda': 'davivienda',
        'bbva': 'bbva',
        'banco de bogota': 'banco_bogota',
        'banco de bogotá': 'banco_bogota',
        'av villas': 'av_villas',
        'banco popular': 'popular',
        'banco de occidente': 'occidente',
        'scotiabank colpatria': 'colpatria',
        'colpatria': 'colpatria',
        'coltefinanciera': 'coltefinanciera',
        'serfinanza': 'serfinanza',
        'ban100': 'ban100',
        'banco finandina': 'finandina',
        'finandina': 'finandina',
        'banco pichincha': 'pichincha',
        'pichincha': 'pichincha',
        'banco falabella': 'falabella',
        'falabella': 'falabella',
        'bancoomeva': 'bancoomeva',
        'gnb sudameris': 'gnb_sudameris',
        'itau': 'itau',
        'itaú': 'itau',
        'banco caja social': 'caja_social',
        'caja social': 'caja_social',
        'lulo bank': 'lulo_bank',
        'nu colombia': 'nubank',
        'nubank': 'nubank',
        'banco agrario': 'agrario',
        'bancamia': 'bancamia',
        'banco w': 'banco_w',
        'mibanco': 'mibanco',
        'mundo mujer': 'mundo_mujer',
        'coopcentral': 'coopcentral',
        'confiar': 'confiar',
        'credifamilia': 'credifamilia',
        'dann regional': 'dann_regional',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8',
        })

    def _get_bank_code(self, bank_name: str) -> str:
        """Obtiene el codigo del banco a partir del nombre"""
        name_lower = bank_name.lower().strip()
        for key, code in self.BANK_CODE_MAP.items():
            if key in name_lower or name_lower in key:
                return code
        # Generar codigo a partir del nombre
        return re.sub(r'[^a-z0-9]', '_', name_lower)

    def _parse_rate(self, text: str) -> Optional[float]:
        """Parsea un texto de tasa a float"""
        if not text:
            return None
        text = text.strip().replace('%', '').replace(',', '.').replace(' ', '')
        text = re.sub(r'[eE]\.?[aA]\.?', '', text)
        try:
            rate = float(text)
            return round(rate, 2)
        except ValueError:
            return None

    def _parse_amount(self, text: str) -> Optional[float]:
        """Parsea un texto de monto a float"""
        if not text:
            return None
        text = text.strip().replace('$', '').replace('.', '').replace(',', '')
        text = text.replace('COP', '').strip()

        # Manejar millones
        match = re.search(r'(\d+(?:\.\d+)?)\s*[mM]', text)
        if match:
            return float(match.group(1)) * 1_000_000

        try:
            return float(re.sub(r'[^\d]', '', text))
        except ValueError:
            return None

    def _parse_term(self, text: str) -> Optional[int]:
        """Parsea un texto de plazo a dias"""
        if not text:
            return None
        text = text.strip().lower()

        # Patron: X dias
        match = re.search(r'(\d+)\s*d[ií]as?', text)
        if match:
            return int(match.group(1))

        # Patron: X meses
        match = re.search(r'(\d+)\s*mes(?:es)?', text)
        if match:
            return int(match.group(1)) * 30

        # Patron: X año(s)
        match = re.search(r'(\d+)\s*a[ñn]os?', text)
        if match:
            return int(match.group(1)) * 365

        # Solo numero
        match = re.search(r'(\d+)', text)
        if match:
            num = int(match.group(1))
            if num <= 24:  # Probablemente meses
                return num * 30
            return num

        return None

    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Obtiene y parsea una pagina"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'lxml')
        except Exception as e:
            logger.error(f"Error obteniendo {url}: {e}")
            return None

    def scrape_monthly_page(self, month_url: str) -> List[CDTRateFromMejorCDT]:
        """
        Extrae tasas de una pagina mensual de MejorCDT
        Ej: https://mejorcdt.com/mejores-cdt-diciembre-2025
        """
        rates = []
        scraped_at = datetime.now().isoformat()

        # Extraer mes del URL
        month_match = re.search(r'mejores-cdt-(\w+-\d{4})', month_url)
        source_month = month_match.group(1) if month_match else 'unknown'

        logger.info(f"Scraping {month_url}...")
        soup = self._get_page(month_url)

        if not soup:
            logger.error(f"No se pudo obtener la pagina: {month_url}")
            return rates

        # Buscar tablas con datos de CDT
        tables = soup.find_all('table')

        for table in tables:
            table_rates = self._extract_rates_from_table(
                table, month_url, source_month, scraped_at
            )
            rates.extend(table_rates)

        # Buscar tarjetas o divs con informacion de bancos
        bank_cards = soup.find_all(['div', 'article'], class_=re.compile(r'bank|card|entidad|cdt', re.I))
        for card in bank_cards:
            card_rates = self._extract_rates_from_card(
                card, month_url, source_month, scraped_at
            )
            rates.extend(card_rates)

        # Buscar en el texto general patrones de tasas
        text_rates = self._extract_rates_from_text(
            soup, month_url, source_month, scraped_at
        )
        rates.extend(text_rates)

        # Eliminar duplicados
        unique_rates = self._deduplicate_rates(rates)

        logger.info(f"Encontradas {len(unique_rates)} tasas en {month_url}")
        return unique_rates

    def _extract_rates_from_table(self, table, source_url: str, source_month: str, scraped_at: str) -> List[CDTRateFromMejorCDT]:
        """Extrae tasas de una tabla HTML"""
        rates = []
        rows = table.find_all('tr')

        if len(rows) < 2:
            return rates

        # Identificar encabezados
        header_row = rows[0]
        headers = [th.get_text().strip().lower() for th in header_row.find_all(['th', 'td'])]

        # Indices de columnas
        bank_col = None
        rate_col = None
        term_col = None
        amount_col = None

        for i, h in enumerate(headers):
            if any(k in h for k in ['banco', 'entidad', 'institucion']):
                bank_col = i
            elif any(k in h for k in ['tasa', 'rate', 'e.a', 'rendimiento', '%']):
                rate_col = i
            elif any(k in h for k in ['plazo', 'dias', 'meses', 'term']):
                term_col = i
            elif any(k in h for k in ['monto', 'inversion', 'minimo']):
                amount_col = i

        # Si no encontramos columnas por header, intentar heuristicas
        if rate_col is None:
            for i, h in enumerate(headers):
                if re.search(r'\d+\s*d[ií]as?', h):
                    term_col = term_col or 0  # Asumir primera columna es banco
                    rate_col = i
                    break

        # Parsear filas de datos
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                continue

            try:
                # Obtener nombre del banco
                bank_name = cells[bank_col].get_text().strip() if bank_col is not None and bank_col < len(cells) else None

                if not bank_name:
                    # Intentar primera celda
                    bank_name = cells[0].get_text().strip()

                if not bank_name or len(bank_name) < 3:
                    continue

                # Buscar tasas en las celdas restantes
                for i, cell in enumerate(cells):
                    if i == bank_col:
                        continue

                    cell_text = cell.get_text().strip()
                    rate = self._parse_rate(cell_text)

                    if rate and 1 < rate < 25:  # Rango razonable para tasas EA
                        # Determinar plazo
                        term_days = 360  # Default
                        if term_col is not None and term_col < len(cells):
                            term_days = self._parse_term(cells[term_col].get_text()) or 360
                        elif i < len(headers):
                            term_days = self._parse_term(headers[i]) or 360

                        # Monto minimo
                        min_amount = None
                        if amount_col is not None and amount_col < len(cells):
                            min_amount = self._parse_amount(cells[amount_col].get_text())

                        rates.append(CDTRateFromMejorCDT(
                            bank_name=bank_name,
                            bank_code=self._get_bank_code(bank_name),
                            rate_ea=rate,
                            term_days=term_days,
                            min_amount=min_amount,
                            max_amount=None,
                            rate_type='fijo',
                            source_url=source_url,
                            source_month=source_month,
                            scraped_at=scraped_at
                        ))

            except Exception as e:
                logger.debug(f"Error parseando fila: {e}")
                continue

        return rates

    def _extract_rates_from_card(self, card, source_url: str, source_month: str, scraped_at: str) -> List[CDTRateFromMejorCDT]:
        """Extrae tasas de una tarjeta/div de banco"""
        rates = []
        text = card.get_text()

        # Buscar nombre del banco
        bank_name = None
        title = card.find(['h2', 'h3', 'h4', 'strong', 'b'])
        if title:
            bank_name = title.get_text().strip()

        if not bank_name or len(bank_name) < 3:
            return rates

        # Buscar patrones de tasa
        rate_matches = re.findall(r'(\d{1,2}[.,]\d{1,2})\s*%?\s*[eE]\.?[aA]\.?', text)

        for rate_str in rate_matches:
            rate = self._parse_rate(rate_str)
            if rate and 1 < rate < 25:
                rates.append(CDTRateFromMejorCDT(
                    bank_name=bank_name,
                    bank_code=self._get_bank_code(bank_name),
                    rate_ea=rate,
                    term_days=360,
                    min_amount=None,
                    max_amount=None,
                    rate_type='fijo',
                    source_url=source_url,
                    source_month=source_month,
                    scraped_at=scraped_at
                ))

        return rates

    def _extract_rates_from_text(self, soup, source_url: str, source_month: str, scraped_at: str) -> List[CDTRateFromMejorCDT]:
        """Extrae tasas mencionadas en el texto de la pagina"""
        rates = []
        text = soup.get_text()

        # Patron: "Banco X ofrece Y% E.A."
        pattern = r'([A-Z][a-záéíóúñ]+(?:\s+[A-Z]?[a-záéíóúñ]+)*)\s+(?:ofrece|tiene|paga)?\s*(\d{1,2}[.,]\d{1,2})\s*%?\s*[eE]\.?[aA]\.?'
        matches = re.findall(pattern, text)

        for bank_name, rate_str in matches:
            if len(bank_name) < 3:
                continue

            rate = self._parse_rate(rate_str)
            if rate and 1 < rate < 25:
                bank_code = self._get_bank_code(bank_name)
                if bank_code in self.BANK_CODE_MAP.values():
                    rates.append(CDTRateFromMejorCDT(
                        bank_name=bank_name,
                        bank_code=bank_code,
                        rate_ea=rate,
                        term_days=360,
                        min_amount=None,
                        max_amount=None,
                        rate_type='fijo',
                        source_url=source_url,
                        source_month=source_month,
                        scraped_at=scraped_at
                    ))

        return rates

    def _deduplicate_rates(self, rates: List[CDTRateFromMejorCDT]) -> List[CDTRateFromMejorCDT]:
        """Elimina tasas duplicadas"""
        seen = set()
        unique = []

        for rate in rates:
            key = (rate.bank_code, rate.term_days, rate.rate_ea)
            if key not in seen:
                seen.add(key)
                unique.append(rate)

        return unique

    def scrape_current_month(self) -> List[CDTRateFromMejorCDT]:
        """Scrapea el mes actual"""
        now = datetime.now()
        months_es = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }
        month_name = months_es[now.month]
        url = f"{self.BASE_URL}/mejores-cdt-{month_name}-{now.year}"
        return self.scrape_monthly_page(url)

    def scrape_multiple_months(self, num_months: int = 3) -> Dict[str, List[CDTRateFromMejorCDT]]:
        """Scrapea multiples meses"""
        results = {}
        now = datetime.now()
        months_es = {
            1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
            5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
            9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
        }

        for i in range(num_months):
            month = now.month - i
            year = now.year
            if month <= 0:
                month += 12
                year -= 1

            month_name = months_es[month]
            url = f"{self.BASE_URL}/mejores-cdt-{month_name}-{year}"
            key = f"{month_name}-{year}"

            rates = self.scrape_monthly_page(url)
            if rates:
                results[key] = rates

            time.sleep(1)  # Rate limiting

        return results

    def get_best_rates(self, rates: List[CDTRateFromMejorCDT], top_n: int = 10) -> List[CDTRateFromMejorCDT]:
        """Obtiene las mejores tasas"""
        sorted_rates = sorted(rates, key=lambda r: r.rate_ea, reverse=True)
        return sorted_rates[:top_n]


def run_mejorcdt_scraping():
    """Ejecuta el scraping de MejorCDT.com"""
    scraper = MejorCDTScraper()

    print("=" * 60)
    print("SCRAPING DE MEJORCDT.COM")
    print("=" * 60)

    # Scrape mes actual
    rates = scraper.scrape_current_month()

    if rates:
        print(f"\nEncontradas {len(rates)} tasas")
        print("\nTOP 10 MEJORES TASAS:")
        print("-" * 60)

        best = scraper.get_best_rates(rates, 10)
        for i, rate in enumerate(best, 1):
            print(f"{i:2}. {rate.bank_name:25} | {rate.term_days:4} dias | {rate.rate_ea:.2f}% E.A.")

        return rates
    else:
        print("No se encontraron tasas")
        return []


if __name__ == '__main__':
    run_mejorcdt_scraping()
