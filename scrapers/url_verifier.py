#!/usr/bin/env python3
"""
Modulo de verificacion de URLs de bancos colombianos
Permite verificar el estado y contenido de cada sitio web de banco
para revision manual del correcto funcionamiento del scraping
"""
import os
import sys
import time
import json
import re
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URLs reales de CDT de bancos colombianos
BANK_URLS = {
    # FUENTE PRINCIPAL CONSOLIDADA
    'mejorcdt': {
        'name': 'MejorCDT.com (Fuente Principal)',
        'main_url': 'https://mejorcdt.com/',
        'rates_url': 'https://mejorcdt.com/mejores-cdt-diciembre-2025',
        'api_url': None,
        'notes': 'FUENTE PRINCIPAL. Datos consolidados mensuales de todos los bancos. Muy confiable.'
    },
    'bancolombia': {
        'name': 'Bancolombia',
        'main_url': 'https://www.bancolombia.com/personas/productos-servicios/inversiones/cdt',
        'rates_url': 'https://www.bancolombia.com/personas/productos-servicios/inversiones/cdt/simulador',
        'api_url': None,
        'notes': 'Usa simulador dinamico con JavaScript'
    },
    'davivienda': {
        'name': 'Davivienda',
        'main_url': 'https://www.davivienda.com/wps/portal/personas/nuevo/personas/quiero_invertir/cdt',
        'rates_url': 'https://www.davivienda.com/wps/portal/personas/nuevo/personas/quiero_invertir/cdt/cdt-tradicional',
        'api_url': None,
        'notes': 'Portal WPS, contenido dinamico'
    },
    'bbva': {
        'name': 'BBVA Colombia',
        'main_url': 'https://www.bbva.com.co/personas/productos/inversion/cdt.html',
        'rates_url': 'https://www.bbva.com.co/personas/productos/inversion/cdt.html',
        'api_url': None,
        'notes': 'Pagina estatica con informacion general'
    },
    'banco_bogota': {
        'name': 'Banco de Bogota',
        'main_url': 'https://www.bancodebogota.com/wps/portal/banco-bogota/bogota/productos/para-ti/inversiones/cdt',
        'rates_url': 'https://www.bancodebogota.com/wps/portal/banco-bogota/bogota/productos/para-ti/inversiones/cdt',
        'api_url': None,
        'notes': 'Portal WPS corporativo'
    },
    'colpatria': {
        'name': 'Scotiabank Colpatria',
        'main_url': 'https://www.scotiabankcolpatria.com/personas/inversiones/cdt',
        'rates_url': 'https://www.scotiabankcolpatria.com/personas/inversiones/cdt',
        'api_url': None,
        'notes': 'Sitio Scotiabank Colombia'
    },
    'av_villas': {
        'name': 'AV Villas',
        'main_url': 'https://www.avvillas.com.co/wps/portal/avvillas/banco/personas/productos/inversiones/cdt',
        'rates_url': 'https://www.avvillas.com.co/wps/portal/avvillas/banco/personas/productos/inversiones/cdt',
        'api_url': None,
        'notes': 'Grupo Aval - Portal WPS'
    },
    'popular': {
        'name': 'Banco Popular',
        'main_url': 'https://www.bancopopular.com.co/wps/portal/popular/inicio/personas/inversiones/cdt',
        'rates_url': 'https://www.bancopopular.com.co/wps/portal/popular/inicio/personas/inversiones/cdt',
        'api_url': None,
        'notes': 'Grupo Aval - Portal WPS'
    },
    'occidente': {
        'name': 'Banco de Occidente',
        'main_url': 'https://www.bancodeoccidente.com.co/wps/portal/banco-occidente/bancodeoccidente/para-personas/inversiones/cdt',
        'rates_url': 'https://www.bancodeoccidente.com.co/wps/portal/banco-occidente/bancodeoccidente/para-personas/inversiones/cdt',
        'api_url': None,
        'notes': 'Grupo Aval - Portal WPS'
    },
    'caja_social': {
        'name': 'Banco Caja Social',
        'main_url': 'https://www.bancocajasocial.com/personas/productos/inversiones/cdt',
        'rates_url': 'https://www.bancocajasocial.com/personas/productos/inversiones/cdt',
        'api_url': None,
        'notes': 'Fundacion Social'
    },
    'itau': {
        'name': 'Itau Colombia',
        'main_url': 'https://www.itau.co/personas/inversiones/cdt',
        'rates_url': 'https://www.itau.co/personas/inversiones/cdt',
        'api_url': None,
        'notes': 'Banco brasileno en Colombia'
    },
    'coltefinanciera': {
        'name': 'Coltefinanciera',
        'main_url': 'https://www.coltefinanciera.com.co/',
        'rates_url': 'https://www.coltefinanciera.com.co/personas/productos/cdt',
        'api_url': None,
        'notes': 'Compania de financiamiento - tasas competitivas'
    },
    'serfinanza': {
        'name': 'Serfinanza',
        'main_url': 'https://www.serfinanza.com.co/',
        'rates_url': 'https://www.serfinanza.com.co/personas/ahorro-e-inversion/cdt/',
        'api_url': None,
        'notes': 'Compania de financiamiento del Grupo Bolivar'
    },
    'finandina': {
        'name': 'Banco Finandina',
        'main_url': 'https://www.bancofinandina.com/',
        'rates_url': 'https://www.bancofinandina.com/personas/cdt',
        'api_url': None,
        'notes': 'Banco digital colombiano'
    },
    'pichincha': {
        'name': 'Banco Pichincha',
        'main_url': 'https://www.bancopichincha.com.co/',
        'rates_url': 'https://www.bancopichincha.com.co/web/personas/cdt',
        'api_url': None,
        'notes': 'Banco ecuatoriano en Colombia'
    },
    'falabella': {
        'name': 'Banco Falabella',
        'main_url': 'https://www.bancofalabella.com.co/',
        'rates_url': 'https://www.bancofalabella.com.co/cdt',
        'api_url': None,
        'notes': 'Banco retail chileno'
    },
    'bancoomeva': {
        'name': 'Bancoomeva',
        'main_url': 'https://www.bancoomeva.com.co/',
        'rates_url': 'https://www.bancoomeva.com.co/publicaciones/102043/cdt/',
        'api_url': None,
        'notes': 'Banco cooperativo'
    },
    'gnb_sudameris': {
        'name': 'GNB Sudameris',
        'main_url': 'https://www.gnbsudameris.com.co/',
        'rates_url': 'https://www.gnbsudameris.com.co/personas/inversiones/cdt',
        'api_url': None,
        'notes': 'Banco del Grupo Gilinski'
    },
    'ban100': {
        'name': 'Ban100',
        'main_url': 'https://www.ban100.com.co/',
        'rates_url': 'https://www.ban100.com.co/ahorro/cdt',
        'api_url': None,
        'notes': 'Banco 100% digital - tasas competitivas'
    },
    'lulo_bank': {
        'name': 'Lulo Bank',
        'main_url': 'https://www.lulobank.com/',
        'rates_url': 'https://www.lulobank.com/cdt',
        'api_url': None,
        'notes': 'Banco digital - Grupo Gilinski'
    },
    'nubank': {
        'name': 'Nu Colombia',
        'main_url': 'https://nu.com.co/',
        'rates_url': 'https://nu.com.co/cajitas/',
        'api_url': None,
        'notes': 'Neobank brasileno - Cajitas de ahorro'
    },
}


@dataclass
class URLVerificationResult:
    """Resultado de verificacion de una URL"""
    bank_code: str
    bank_name: str
    url: str
    url_type: str  # 'main', 'rates', 'api'
    status_code: int
    is_accessible: bool
    response_time_ms: float
    content_length: int
    has_cdt_content: bool
    cdt_keywords_found: List[str]
    rate_patterns_found: List[str]
    requires_javascript: bool
    error_message: Optional[str]
    verified_at: str
    page_title: str
    meta_description: str

    def to_dict(self) -> Dict:
        return asdict(self)


class URLVerifier:
    """Verificador de URLs de bancos"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-CO,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })

        # Palabras clave para detectar contenido de CDT
        self.cdt_keywords = [
            'cdt', 'certificado', 'deposito', 'termino', 'inversion',
            'tasa', 'plazo', 'rendimiento', 'e.a.', 'efectivo anual',
            'rentabilidad', 'intereses', 'ahorro'
        ]

        # Patrones para detectar tasas
        self.rate_patterns = [
            r'\d{1,2}[.,]\d{1,2}\s*%',  # 12.5%, 8,5%
            r'\d{1,2}[.,]\d{1,2}\s*E\.?A\.?',  # 12.5 E.A., 8,5EA
            r'tasa[:\s]+\d{1,2}[.,]\d{1,2}',  # tasa: 12.5
        ]

    def verify_url(self, bank_code: str, url: str, url_type: str = 'main') -> URLVerificationResult:
        """Verifica una URL especifica"""
        bank_info = BANK_URLS.get(bank_code, {})
        bank_name = bank_info.get('name', bank_code)

        result = URLVerificationResult(
            bank_code=bank_code,
            bank_name=bank_name,
            url=url,
            url_type=url_type,
            status_code=0,
            is_accessible=False,
            response_time_ms=0,
            content_length=0,
            has_cdt_content=False,
            cdt_keywords_found=[],
            rate_patterns_found=[],
            requires_javascript=False,
            error_message=None,
            verified_at=datetime.now().isoformat(),
            page_title='',
            meta_description=''
        )

        try:
            start_time = time.time()
            response = self.session.get(url, timeout=30, allow_redirects=True)
            result.response_time_ms = (time.time() - start_time) * 1000
            result.status_code = response.status_code
            result.is_accessible = response.status_code == 200
            result.content_length = len(response.content)

            if result.is_accessible:
                soup = BeautifulSoup(response.content, 'lxml')
                text_content = soup.get_text().lower()

                # Obtener titulo y meta description
                title_tag = soup.find('title')
                result.page_title = title_tag.get_text().strip() if title_tag else ''

                meta_desc = soup.find('meta', attrs={'name': 'description'})
                result.meta_description = meta_desc.get('content', '') if meta_desc else ''

                # Buscar palabras clave de CDT
                for keyword in self.cdt_keywords:
                    if keyword in text_content:
                        result.cdt_keywords_found.append(keyword)

                result.has_cdt_content = len(result.cdt_keywords_found) >= 3

                # Buscar patrones de tasas
                for pattern in self.rate_patterns:
                    matches = re.findall(pattern, text_content, re.IGNORECASE)
                    result.rate_patterns_found.extend(matches[:5])  # Limitar a 5

                # Detectar si requiere JavaScript
                scripts = soup.find_all('script')
                noscript = soup.find('noscript')
                js_frameworks = ['react', 'angular', 'vue', 'next', 'nuxt']

                for script in scripts:
                    src = script.get('src', '').lower()
                    content = script.string or ''
                    if any(fw in src or fw in content.lower() for fw in js_frameworks):
                        result.requires_javascript = True
                        break

                if noscript and 'javascript' in noscript.get_text().lower():
                    result.requires_javascript = True

        except requests.exceptions.Timeout:
            result.error_message = "Timeout - La pagina tardo mas de 30 segundos"
        except requests.exceptions.SSLError as e:
            result.error_message = f"Error SSL: {str(e)[:100]}"
        except requests.exceptions.ConnectionError as e:
            result.error_message = f"Error de conexion: {str(e)[:100]}"
        except Exception as e:
            result.error_message = f"Error: {str(e)[:100]}"

        return result

    def verify_bank(self, bank_code: str) -> List[URLVerificationResult]:
        """Verifica todas las URLs de un banco"""
        results = []
        bank_info = BANK_URLS.get(bank_code)

        if not bank_info:
            logger.warning(f"Banco no encontrado: {bank_code}")
            return results

        # Verificar URL principal
        if bank_info.get('main_url'):
            result = self.verify_url(bank_code, bank_info['main_url'], 'main')
            results.append(result)

        # Verificar URL de tasas
        if bank_info.get('rates_url') and bank_info['rates_url'] != bank_info.get('main_url'):
            result = self.verify_url(bank_code, bank_info['rates_url'], 'rates')
            results.append(result)

        # Verificar API si existe
        if bank_info.get('api_url'):
            result = self.verify_url(bank_code, bank_info['api_url'], 'api')
            results.append(result)

        return results

    def verify_all_banks(self, parallel: bool = True) -> Dict[str, List[URLVerificationResult]]:
        """Verifica todos los bancos"""
        all_results = {}

        if parallel:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(self.verify_bank, code): code
                    for code in BANK_URLS.keys()
                }

                for future in as_completed(futures):
                    bank_code = futures[future]
                    try:
                        results = future.result()
                        all_results[bank_code] = results
                    except Exception as e:
                        logger.error(f"Error verificando {bank_code}: {e}")
        else:
            for bank_code in BANK_URLS.keys():
                results = self.verify_bank(bank_code)
                all_results[bank_code] = results
                time.sleep(1)  # Rate limiting

        return all_results


def generate_report(results: Dict[str, List[URLVerificationResult]], output_format: str = 'text') -> str:
    """Genera un reporte de verificacion"""

    if output_format == 'json':
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'total_banks': len(results),
            'banks': {}
        }
        for bank_code, bank_results in results.items():
            report_data['banks'][bank_code] = [r.to_dict() for r in bank_results]
        return json.dumps(report_data, indent=2, ensure_ascii=False)

    # Formato texto
    lines = []
    lines.append("=" * 80)
    lines.append("REPORTE DE VERIFICACION DE URLs DE BANCOS - CDT COLOMBIA")
    lines.append(f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)

    # Estadisticas generales
    total_urls = sum(len(r) for r in results.values())
    accessible = sum(1 for bank_results in results.values() for r in bank_results if r.is_accessible)
    with_cdt = sum(1 for bank_results in results.values() for r in bank_results if r.has_cdt_content)
    with_rates = sum(1 for bank_results in results.values() for r in bank_results if r.rate_patterns_found)

    lines.append(f"\nESTADISTICAS GENERALES:")
    lines.append(f"  Total bancos: {len(results)}")
    lines.append(f"  Total URLs verificadas: {total_urls}")
    lines.append(f"  URLs accesibles: {accessible} ({accessible/total_urls*100:.1f}%)")
    lines.append(f"  URLs con contenido CDT: {with_cdt} ({with_cdt/total_urls*100:.1f}%)")
    lines.append(f"  URLs con tasas detectadas: {with_rates} ({with_rates/total_urls*100:.1f}%)")

    lines.append("\n" + "-" * 80)
    lines.append("DETALLE POR BANCO:")
    lines.append("-" * 80)

    for bank_code, bank_results in sorted(results.items()):
        bank_info = BANK_URLS.get(bank_code, {})
        lines.append(f"\n{'='*60}")
        lines.append(f"BANCO: {bank_info.get('name', bank_code)}")
        lines.append(f"Codigo: {bank_code}")
        lines.append(f"Notas: {bank_info.get('notes', 'N/A')}")
        lines.append(f"{'='*60}")

        for result in bank_results:
            status_icon = "[OK]" if result.is_accessible else "[ERROR]"
            cdt_icon = "[CDT]" if result.has_cdt_content else "[---]"
            rate_icon = "[TASAS]" if result.rate_patterns_found else "[-----]"
            js_icon = "[JS]" if result.requires_javascript else "[--]"

            lines.append(f"\n  URL ({result.url_type}): {result.url}")
            lines.append(f"  Estado: {status_icon} HTTP {result.status_code} | {cdt_icon} | {rate_icon} | {js_icon}")
            lines.append(f"  Tiempo respuesta: {result.response_time_ms:.0f}ms | Tamaño: {result.content_length/1024:.1f}KB")

            if result.page_title:
                lines.append(f"  Titulo: {result.page_title[:60]}...")

            if result.error_message:
                lines.append(f"  ERROR: {result.error_message}")

            if result.cdt_keywords_found:
                lines.append(f"  Keywords CDT: {', '.join(result.cdt_keywords_found[:5])}")

            if result.rate_patterns_found:
                lines.append(f"  Tasas encontradas: {', '.join(result.rate_patterns_found[:5])}")

            if result.requires_javascript:
                lines.append(f"  NOTA: Requiere JavaScript/navegador para contenido dinamico")

    # Resumen de problemas
    lines.append("\n" + "=" * 80)
    lines.append("RESUMEN DE PROBLEMAS:")
    lines.append("=" * 80)

    problems = []
    for bank_code, bank_results in results.items():
        bank_name = BANK_URLS.get(bank_code, {}).get('name', bank_code)
        for result in bank_results:
            if not result.is_accessible:
                problems.append(f"  - {bank_name}: URL no accesible ({result.url_type})")
            elif not result.has_cdt_content:
                problems.append(f"  - {bank_name}: Sin contenido CDT detectado ({result.url_type})")
            elif result.requires_javascript and not result.rate_patterns_found:
                problems.append(f"  - {bank_name}: Requiere Selenium para scraping ({result.url_type})")

    if problems:
        lines.extend(problems)
    else:
        lines.append("  No se detectaron problemas criticos")

    # Recomendaciones
    lines.append("\n" + "=" * 80)
    lines.append("RECOMENDACIONES PARA SCRAPING:")
    lines.append("=" * 80)

    for bank_code, bank_results in results.items():
        bank_name = BANK_URLS.get(bank_code, {}).get('name', bank_code)
        for result in bank_results:
            if result.url_type == 'rates' and result.is_accessible:
                if result.rate_patterns_found and not result.requires_javascript:
                    lines.append(f"  [FACIL] {bank_name}: Scraping estatico posible")
                elif result.rate_patterns_found and result.requires_javascript:
                    lines.append(f"  [MEDIO] {bank_name}: Requiere Selenium")
                elif result.requires_javascript:
                    lines.append(f"  [DIFICIL] {bank_name}: JS dinamico, posible API interna")
                else:
                    lines.append(f"  [REVISAR] {bank_name}: Verificar manualmente")

    lines.append("\n" + "=" * 80)

    return "\n".join(lines)


def save_report(results: Dict[str, List[URLVerificationResult]], output_dir: str = None):
    """Guarda el reporte en archivos"""
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Guardar JSON
    json_path = os.path.join(output_dir, f'url_verification_{timestamp}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(generate_report(results, 'json'))
    logger.info(f"Reporte JSON guardado: {json_path}")

    # Guardar texto
    txt_path = os.path.join(output_dir, f'url_verification_{timestamp}.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(generate_report(results, 'text'))
    logger.info(f"Reporte TXT guardado: {txt_path}")

    return json_path, txt_path


def verify_single_bank(bank_code: str):
    """Verifica un solo banco y muestra resultados"""
    verifier = URLVerifier()
    results = verifier.verify_bank(bank_code)

    if not results:
        print(f"Banco '{bank_code}' no encontrado")
        print(f"Bancos disponibles: {', '.join(BANK_URLS.keys())}")
        return

    print(generate_report({bank_code: results}, 'text'))


def verify_all():
    """Verifica todos los bancos"""
    verifier = URLVerifier()
    print("Verificando URLs de todos los bancos...")
    print("Esto puede tomar unos minutos...\n")

    results = verifier.verify_all_banks(parallel=True)
    report = generate_report(results, 'text')
    print(report)

    # Guardar reportes
    json_path, txt_path = save_report(results)
    print(f"\nReportes guardados en:")
    print(f"  - {json_path}")
    print(f"  - {txt_path}")


def list_banks():
    """Lista todos los bancos disponibles"""
    print("\n" + "=" * 60)
    print("BANCOS DISPONIBLES PARA VERIFICACION")
    print("=" * 60)

    for code, info in sorted(BANK_URLS.items()):
        print(f"\n{info['name']} ({code})")
        print(f"  URL Principal: {info['main_url']}")
        if info.get('rates_url') and info['rates_url'] != info['main_url']:
            print(f"  URL Tasas: {info['rates_url']}")
        print(f"  Notas: {info.get('notes', 'N/A')}")

    print("\n" + "=" * 60)


def main():
    """Funcion principal"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Verificador de URLs de bancos colombianos para CDT'
    )
    parser.add_argument(
        'command',
        choices=['all', 'bank', 'list'],
        help='Comando: all (verificar todos), bank (verificar uno), list (listar bancos)'
    )
    parser.add_argument(
        '--bank', '-b',
        help='Codigo del banco a verificar (usar con comando "bank")'
    )

    args = parser.parse_args()

    if args.command == 'all':
        verify_all()
    elif args.command == 'bank':
        if not args.bank:
            print("Error: Debes especificar un banco con --bank")
            print(f"Bancos disponibles: {', '.join(BANK_URLS.keys())}")
            sys.exit(1)
        verify_single_bank(args.bank)
    elif args.command == 'list':
        list_banks()


if __name__ == '__main__':
    main()
