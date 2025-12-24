"""
Clase base para scrapers de bancos
"""
import time
import json
import logging
import hashlib
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from .config import BankConfig, SCRAPING_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CDTRate:
    """Representa una tasa de CDT"""
    bank_code: str
    bank_name: str
    term_days: int
    rate_ea: float  # Tasa Efectiva Anual
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    rate_type: str = 'fijo'  # 'fijo', 'variable'
    payment_frequency: str = 'vencimiento'  # 'mensual', 'trimestral', 'vencimiento'
    investment_type: str = 'CDT'  # 'CDT', 'Derechos Fiduciarios', 'Finca Raiz'
    special_conditions: Optional[str] = None
    source_url: str = ''
    scraped_at: str = ''

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ScrapingResult:
    """Resultado del scraping de un banco"""
    bank_code: str
    bank_name: str
    success: bool
    rates: List[CDTRate]
    error_message: Optional[str] = None
    scraped_at: str = ''
    scraping_duration: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'bank_code': self.bank_code,
            'bank_name': self.bank_name,
            'success': self.success,
            'rates': [r.to_dict() for r in self.rates],
            'error_message': self.error_message,
            'scraped_at': self.scraped_at,
            'scraping_duration': self.scraping_duration
        }


class BaseScraper(ABC):
    """Clase base para todos los scrapers de bancos"""

    def __init__(self, config: BankConfig):
        self.config = config
        self.session = requests.Session()
        self.ua = UserAgent()
        self._setup_session()

    def _setup_session(self):
        """Configura la sesion HTTP con headers apropiados"""
        self.session.headers.update({
            'User-Agent': self.ua.random if SCRAPING_CONFIG['user_agent_rotation'] else self.ua.chrome,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        })

    def _get_page(self, url: str, params: Dict = None) -> Optional[BeautifulSoup]:
        """Obtiene y parsea una pagina web"""
        for attempt in range(SCRAPING_CONFIG['retry_attempts']):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=SCRAPING_CONFIG['default_timeout']
                )
                response.raise_for_status()
                return BeautifulSoup(response.content, 'lxml')
            except requests.RequestException as e:
                logger.warning(f"Intento {attempt + 1} fallido para {url}: {e}")
                if attempt < SCRAPING_CONFIG['retry_attempts'] - 1:
                    time.sleep(SCRAPING_CONFIG['retry_delay'])
        return None

    def _post_page(self, url: str, data: Dict = None, json_data: Dict = None) -> Optional[Any]:
        """Envia POST request"""
        for attempt in range(SCRAPING_CONFIG['retry_attempts']):
            try:
                response = self.session.post(
                    url,
                    data=data,
                    json=json_data,
                    timeout=SCRAPING_CONFIG['default_timeout']
                )
                response.raise_for_status()

                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    return response.json()
                return BeautifulSoup(response.content, 'lxml')
            except requests.RequestException as e:
                logger.warning(f"POST intento {attempt + 1} fallido para {url}: {e}")
                if attempt < SCRAPING_CONFIG['retry_attempts'] - 1:
                    time.sleep(SCRAPING_CONFIG['retry_delay'])
        return None

    def _parse_rate(self, text: str) -> Optional[float]:
        """Parsea un texto de tasa a float"""
        if not text:
            return None
        # Limpiar el texto
        text = text.strip().replace('%', '').replace(',', '.').replace(' ', '')
        text = text.replace('E.A.', '').replace('EA', '').replace('e.a.', '')
        try:
            rate = float(text)
            # Si la tasa es mayor a 1, asumimos que esta en porcentaje
            if rate > 1:
                rate = rate / 100
            return round(rate * 100, 2)  # Retornar en porcentaje
        except ValueError:
            return None

    def _parse_amount(self, text: str) -> Optional[float]:
        """Parsea un texto de monto a float"""
        if not text:
            return None
        text = text.strip().replace('$', '').replace('.', '').replace(',', '')
        text = text.replace('COP', '').replace('cop', '').strip()
        # Manejar millones
        if 'M' in text.upper():
            text = text.upper().replace('M', '').strip()
            try:
                return float(text) * 1_000_000
            except ValueError:
                return None
        try:
            return float(text)
        except ValueError:
            return None

    def _parse_term(self, text: str) -> Optional[int]:
        """Parsea un texto de plazo a dias"""
        if not text:
            return None
        text = text.strip().lower()

        # Buscar patrones comunes
        import re

        # Patron: X dias
        match = re.search(r'(\d+)\s*d[ií]as?', text)
        if match:
            return int(match.group(1))

        # Patron: X meses
        match = re.search(r'(\d+)\s*mes(?:es)?', text)
        if match:
            return int(match.group(1)) * 30

        # Patron: X anos
        match = re.search(r'(\d+)\s*a[ñn]os?', text)
        if match:
            return int(match.group(1)) * 365

        # Solo numero
        match = re.search(r'(\d+)', text)
        if match:
            num = int(match.group(1))
            # Heuristicas
            if num <= 36:  # Probablemente meses
                return num * 30
            return num  # Probablemente dias

        return None

    @abstractmethod
    def scrape(self) -> ScrapingResult:
        """Metodo abstracto que cada scraper debe implementar"""
        pass

    def run(self) -> ScrapingResult:
        """Ejecuta el scraper con manejo de errores y timing"""
        start_time = time.time()
        scraped_at = datetime.now().isoformat()

        try:
            logger.info(f"Iniciando scraping de {self.config.name}...")
            result = self.scrape()
            result.scraped_at = scraped_at
            result.scraping_duration = time.time() - start_time

            # Actualizar timestamp en cada rate
            for rate in result.rates:
                rate.scraped_at = scraped_at

            logger.info(f"Scraping de {self.config.name} completado: {len(result.rates)} tasas encontradas")
            return result

        except Exception as e:
            logger.error(f"Error scraping {self.config.name}: {e}")
            return ScrapingResult(
                bank_code=self.config.code,
                bank_name=self.config.name,
                success=False,
                rates=[],
                error_message=str(e),
                scraped_at=scraped_at,
                scraping_duration=time.time() - start_time
            )


class SeleniumScraper(BaseScraper):
    """Scraper base que usa Selenium para paginas dinamicas"""

    def __init__(self, config: BankConfig):
        super().__init__(config)
        self.driver = None

    def _init_driver(self):
        """Inicializa el driver de Selenium"""
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager

        options = Options()
        if SCRAPING_CONFIG['headless_browser']:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--user-agent={self.ua.random}')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)

    def _close_driver(self):
        """Cierra el driver de Selenium"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def _get_page_selenium(self, url: str, wait_time: int = 5) -> Optional[BeautifulSoup]:
        """Obtiene una pagina usando Selenium"""
        try:
            if not self.driver:
                self._init_driver()

            self.driver.get(url)
            time.sleep(wait_time)  # Esperar carga dinamica

            return BeautifulSoup(self.driver.page_source, 'lxml')
        except Exception as e:
            logger.error(f"Error Selenium para {url}: {e}")
            return None
