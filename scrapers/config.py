"""
Configuracion para el sistema de scraping de CDTs
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class BankConfig:
    """Configuracion de cada banco"""
    name: str
    code: str
    url: str
    scraper_type: str  # 'static', 'dynamic', 'api'
    enabled: bool = True
    requires_selenium: bool = False
    rate_limit_seconds: float = 2.0

# Configuracion de bancos colombianos
BANKS_CONFIG = {
    'bancolombia': BankConfig(
        name='Bancolombia',
        code='bancolombia',
        url='https://www.bancolombia.com/personas/productos-servicios/inversiones/cdt',
        scraper_type='dynamic',
        requires_selenium=True
    ),
    'davivienda': BankConfig(
        name='Davivienda',
        code='davivienda',
        url='https://www.davivienda.com/wps/portal/personas/nuevo/personas/quiero_invertir/cdt',
        scraper_type='dynamic',
        requires_selenium=True
    ),
    'bbva': BankConfig(
        name='BBVA Colombia',
        code='bbva',
        url='https://www.bbva.com.co/personas/productos/inversion/cdt.html',
        scraper_type='static'
    ),
    'banco_bogota': BankConfig(
        name='Banco de Bogota',
        code='banco_bogota',
        url='https://www.bancodebogota.com/wps/portal/banco-bogota/bogota/productos/para-ti/inversiones/cdt',
        scraper_type='dynamic',
        requires_selenium=True
    ),
    'colpatria': BankConfig(
        name='Scotiabank Colpatria',
        code='colpatria',
        url='https://www.scotiabankcolpatria.com/personas/inversiones/cdt',
        scraper_type='static'
    ),
    'av_villas': BankConfig(
        name='AV Villas',
        code='av_villas',
        url='https://www.avvillas.com.co/wps/portal/avvillas/banco/personas/productos/inversiones/cdt',
        scraper_type='dynamic',
        requires_selenium=True
    ),
    'popular': BankConfig(
        name='Banco Popular',
        code='popular',
        url='https://www.bancopopular.com.co/wps/portal/popular/inicio/personas/inversiones/cdt',
        scraper_type='dynamic',
        requires_selenium=True
    ),
    'caja_social': BankConfig(
        name='Banco Caja Social',
        code='caja_social',
        url='https://www.bancocajasocial.com/personas/productos/inversiones/cdt',
        scraper_type='static'
    ),
    'occidente': BankConfig(
        name='Banco de Occidente',
        code='occidente',
        url='https://www.bancodeoccidente.com.co/wps/portal/banco-occidente/bancodeoccidente/para-personas/inversiones/cdt',
        scraper_type='dynamic',
        requires_selenium=True
    ),
    'itau': BankConfig(
        name='Itau',
        code='itau',
        url='https://www.itau.co/personas/inversiones/cdt',
        scraper_type='static'
    ),
    'coltefinanciera': BankConfig(
        name='Coltefinanciera',
        code='coltefinanciera',
        url='https://www.coltefinanciera.com.co/productos/cdt',
        scraper_type='static'
    ),
    'serfinanza': BankConfig(
        name='Serfinanza',
        code='serfinanza',
        url='https://www.serfinanza.com.co/cdt',
        scraper_type='static'
    ),
    'ban100': BankConfig(
        name='Ban100',
        code='ban100',
        url='https://www.ban100.com.co/cdt',
        scraper_type='static'
    ),
    'finandina': BankConfig(
        name='Banco Finandina',
        code='finandina',
        url='https://www.bancofinandina.com/personas/cdt',
        scraper_type='static'
    ),
    'pichincha': BankConfig(
        name='Banco Pichincha',
        code='pichincha',
        url='https://www.bancopichincha.com.co/web/personas/cdt',
        scraper_type='static'
    ),
    'falabella': BankConfig(
        name='Banco Falabella',
        code='falabella',
        url='https://www.bancofalabella.com.co/cdt',
        scraper_type='dynamic',
        requires_selenium=True
    ),
    'bancoomeva': BankConfig(
        name='Bancoomeva',
        code='bancoomeva',
        url='https://www.bancoomeva.com.co/personas/inversiones/cdt',
        scraper_type='static'
    ),
    'gnb_sudameris': BankConfig(
        name='GNB Sudameris',
        code='gnb_sudameris',
        url='https://www.gnbsudameris.com.co/personas/inversiones/cdt',
        scraper_type='static'
    ),
    'atomyrent': BankConfig(
        name='Atomy Rent',
        code='atomyrent',
        url='https://atomyrent.com/',
        scraper_type='static'
    ),
    'finca_raiz': BankConfig(
        name='Finca Raiz Colombia',
        code='finca_raiz',
        url='https://www.fedelonjas.org.co/',
        scraper_type='static'
    ),
    'nubank': BankConfig(
        name='Nubank (Cajitas)',
        code='nubank',
        url='https://nu.com.co/',
        scraper_type='static'
    ),
    'pibank': BankConfig(
        name='Pibank',
        code='pibank',
        url='https://www.pibank.co/',
        scraper_type='static'
    ),
    'lulobank': BankConfig(
        name='Lulo Bank',
        code='lulobank',
        url='https://www.lulobank.com/',
        scraper_type='static'
    ),
}

# Plazos estandar para CDTs (en dias)
STANDARD_TERMS = [30, 60, 90, 180, 360, 540, 720]

# Montos estandar para simulacion
STANDARD_AMOUNTS = [1_000_000, 5_000_000, 10_000_000, 50_000_000, 100_000_000]

# Configuracion de scraping
SCRAPING_CONFIG = {
    'user_agent_rotation': True,
    'default_timeout': 30,
    'retry_attempts': 3,
    'retry_delay': 5,
    'headless_browser': True,
}

# Paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
RATES_FILE = os.path.join(DATA_DIR, 'rates.json')
HISTORY_DIR = os.path.join(DATA_DIR, 'history')
