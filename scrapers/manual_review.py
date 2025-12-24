#!/usr/bin/env python3
"""
Modulo de revision manual para verificar el scraping de CDTs
Proporciona herramientas para revisar y actualizar URLs manualmente
"""
import os
import sys
import json
import webbrowser
from datetime import datetime
from typing import Dict, List, Optional
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

# URLs actualizadas y verificadas de CDT de bancos colombianos
VERIFIED_BANK_URLS = {
    # === FUENTE PRINCIPAL CONSOLIDADA ===
    'mejorcdt': {
        'name': 'MejorCDT.com (Fuente Principal)',
        'urls': {
            'main': 'https://mejorcdt.com/',
            'diciembre_2025': 'https://mejorcdt.com/mejores-cdt-diciembre-2025',
            'noviembre_2025': 'https://mejorcdt.com/mejores-cdt-noviembre-2025',
            'octubre_2025': 'https://mejorcdt.com/mejores-cdt-octubre-2025',
            'simulador': 'https://mejorcdt.com/cdt-simulador',
            'ranking': 'https://mejorcdt.com/ranking-cdt',
        },
        'scraping_method': 'static',
        'difficulty': 'easy',
        'notes': 'FUENTE PRINCIPAL. Datos consolidados de todos los bancos. Actualizacion mensual. Informacion confiable.',
        'last_verified': '2025-12-24',
        'status': 'primary_source'
    },

    # === BANCOS TRADICIONALES GRANDES ===
    'bancolombia': {
        'name': 'Bancolombia',
        'urls': {
            'main': 'https://www.bancolombia.com/personas/productos-servicios/inversiones/cdt',
            'simulator': 'https://www.bancolombia.com/personas/productos-servicios/inversiones/cdt/simulador',
            'rates_pdf': 'https://www.bancolombia.com/wcm/connect/www.bancolombia.com/cdts/tasas',
        },
        'scraping_method': 'selenium',
        'difficulty': 'hard',
        'notes': 'Simulador dinamico con React. Posible API interna.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },
    'davivienda': {
        'name': 'Davivienda',
        'urls': {
            'main': 'https://www.davivienda.com/wps/portal/personas/nuevo/personas/quiero_invertir/cdt',
            'digital': 'https://www.davivienda.com/wps/portal/personas/nuevo/personas/quiero_invertir/cdt/cdt-digital',
        },
        'scraping_method': 'selenium',
        'difficulty': 'hard',
        'notes': 'Portal WPS IBM. Contenido cargado dinamicamente.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },
    'bbva': {
        'name': 'BBVA Colombia',
        'urls': {
            'main': 'https://www.bbva.com.co/personas/productos/inversion/cdt.html',
            'simulator': 'https://www.bbva.com.co/personas/productos/inversion/simuladores/simulador-cdt.html',
        },
        'scraping_method': 'static',
        'difficulty': 'medium',
        'notes': 'Pagina mas estatica. Simulador requiere JS.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },

    # === GRUPO AVAL ===
    'banco_bogota': {
        'name': 'Banco de Bogota',
        'urls': {
            'main': 'https://www.bancodebogota.com/wps/portal/banco-bogota/bogota/productos/para-ti/inversiones/cdt',
        },
        'scraping_method': 'selenium',
        'difficulty': 'hard',
        'notes': 'Grupo Aval. Portal WPS.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },
    'av_villas': {
        'name': 'AV Villas',
        'urls': {
            'main': 'https://www.avvillas.com.co/wps/portal/avvillas/banco/personas/productos/inversiones/cdt',
        },
        'scraping_method': 'selenium',
        'difficulty': 'hard',
        'notes': 'Grupo Aval. Similar a Banco de Bogota.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },
    'popular': {
        'name': 'Banco Popular',
        'urls': {
            'main': 'https://www.bancopopular.com.co/wps/portal/popular/inicio/personas/inversiones/cdt',
        },
        'scraping_method': 'selenium',
        'difficulty': 'hard',
        'notes': 'Grupo Aval. Estructura similar.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },
    'occidente': {
        'name': 'Banco de Occidente',
        'urls': {
            'main': 'https://www.bancodeoccidente.com.co/wps/portal/banco-occidente/bancodeoccidente/para-personas/inversiones/cdt',
        },
        'scraping_method': 'selenium',
        'difficulty': 'hard',
        'notes': 'Grupo Aval.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },

    # === BANCOS DIGITALES / FINTECH (Mejores tasas) ===
    'coltefinanciera': {
        'name': 'Coltefinanciera',
        'urls': {
            'main': 'https://www.coltefinanciera.com.co/',
            'cdt': 'https://www.coltefinanciera.com.co/personas/cdt/',
            'simulator': 'https://www.coltefinanciera.com.co/simuladores/',
        },
        'scraping_method': 'selenium',
        'difficulty': 'medium',
        'notes': 'Compania de financiamiento. Tasas altas. React/Next.js',
        'last_verified': '2025-12-24',
        'status': 'active'
    },
    'serfinanza': {
        'name': 'Serfinanza',
        'urls': {
            'main': 'https://www.serfinanza.com.co/',
            'cdt': 'https://www.serfinanza.com.co/personas/ahorro-e-inversion/cdt/',
        },
        'scraping_method': 'static',
        'difficulty': 'medium',
        'notes': 'Grupo Bolivar. Tasas competitivas.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },
    'ban100': {
        'name': 'Ban100',
        'urls': {
            'main': 'https://www.ban100.com.co/',
            'cdt': 'https://www.ban100.com.co/ahorro/cdt',
            'app': 'https://app.ban100.com.co/',
        },
        'scraping_method': 'api',
        'difficulty': 'medium',
        'notes': 'Banco 100% digital. Posible API REST.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },
    'lulo_bank': {
        'name': 'Lulo Bank',
        'urls': {
            'main': 'https://www.lulobank.com/',
            'cdt': 'https://www.lulobank.com/cdt',
        },
        'scraping_method': 'selenium',
        'difficulty': 'medium',
        'notes': 'Banco digital Gilinski. SPA React.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },
    'nubank': {
        'name': 'Nu Colombia',
        'urls': {
            'main': 'https://nu.com.co/',
            'cajitas': 'https://nu.com.co/cajitas/',
        },
        'scraping_method': 'selenium',
        'difficulty': 'hard',
        'notes': 'Neobank brasileno. Cajitas = CDT equivalente.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },

    # === BANCOS INTERNACIONALES ===
    'colpatria': {
        'name': 'Scotiabank Colpatria',
        'urls': {
            'main': 'https://www.scotiabankcolpatria.com/personas/inversiones/cdt',
        },
        'scraping_method': 'selenium',
        'difficulty': 'medium',
        'notes': 'Banco canadiense en Colombia.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },
    'itau': {
        'name': 'Itau Colombia',
        'urls': {
            'main': 'https://www.itau.co/personas/inversiones',
            'cdt': 'https://www.itau.co/personas/inversiones/cdt',
        },
        'scraping_method': 'static',
        'difficulty': 'medium',
        'notes': 'Banco brasileno. Pagina relativamente estatica.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },
    'pichincha': {
        'name': 'Banco Pichincha',
        'urls': {
            'main': 'https://www.bancopichincha.com.co/',
            'cdt': 'https://www.bancopichincha.com.co/web/personas/cdt',
        },
        'scraping_method': 'selenium',
        'difficulty': 'medium',
        'notes': 'Banco ecuatoriano.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },
    'gnb_sudameris': {
        'name': 'GNB Sudameris',
        'urls': {
            'main': 'https://www.gnbsudameris.com.co/',
            'personas': 'https://www.gnbsudameris.com.co/personas',
        },
        'scraping_method': 'selenium',
        'difficulty': 'medium',
        'notes': 'Grupo Gilinski.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },

    # === OTROS BANCOS ===
    'finandina': {
        'name': 'Banco Finandina',
        'urls': {
            'main': 'https://www.bancofinandina.com/',
            'cdt': 'https://www.bancofinandina.com/personas/cdt',
        },
        'scraping_method': 'selenium',
        'difficulty': 'medium',
        'notes': 'Banco digital colombiano.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },
    'falabella': {
        'name': 'Banco Falabella',
        'urls': {
            'main': 'https://www.bancofalabella.com.co/',
            'cdt': 'https://www.bancofalabella.com.co/inversiones',
        },
        'scraping_method': 'selenium',
        'difficulty': 'hard',
        'notes': 'Banco retail chileno. SPA.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },
    'bancoomeva': {
        'name': 'Bancoomeva',
        'urls': {
            'main': 'https://www.bancoomeva.com.co/',
            'cdt': 'https://www.bancoomeva.com.co/publicaciones/102043/cdt/',
        },
        'scraping_method': 'static',
        'difficulty': 'easy',
        'notes': 'Banco cooperativo. CMS tradicional.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },
    'caja_social': {
        'name': 'Banco Caja Social',
        'urls': {
            'main': 'https://www.bancocajasocial.com/',
            'cdt': 'https://www.bancocajasocial.com/ahorro-e-inversion/cdt',
        },
        'scraping_method': 'selenium',
        'difficulty': 'medium',
        'notes': 'Fundacion Social.',
        'last_verified': '2025-12-24',
        'status': 'active'
    },
}


def generate_review_html() -> str:
    """Genera una pagina HTML para revision manual"""
    html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Revision Manual de URLs - CDT Colombia</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 {
            text-align: center;
            color: #1e3a8a;
            margin-bottom: 10px;
        }
        .subtitle {
            text-align: center;
            color: #64748b;
            margin-bottom: 30px;
        }
        .filters {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            align-items: center;
        }
        .filters label { font-weight: 600; }
        .filters select, .filters input {
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-value { font-size: 2rem; font-weight: 800; color: #1e3a8a; }
        .stat-label { color: #64748b; font-size: 0.9rem; }
        .banks-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
        }
        .bank-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .bank-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }
        .bank-name { font-size: 1.2rem; font-weight: 700; color: #1e3a8a; }
        .bank-code { color: #64748b; font-size: 0.85rem; }
        .difficulty {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .difficulty.easy { background: #dcfce7; color: #166534; }
        .difficulty.medium { background: #fef3c7; color: #92400e; }
        .difficulty.hard { background: #fee2e2; color: #991b1b; }
        .urls-list { margin: 15px 0; }
        .url-item {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 8px 0;
            padding: 8px;
            background: #f8fafc;
            border-radius: 5px;
        }
        .url-type {
            background: #e0e7ff;
            color: #3730a3;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.75rem;
            font-weight: 600;
            min-width: 60px;
            text-align: center;
        }
        .url-link {
            flex: 1;
            color: #2563eb;
            text-decoration: none;
            font-size: 0.85rem;
            word-break: break-all;
        }
        .url-link:hover { text-decoration: underline; }
        .open-btn {
            background: #2563eb;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8rem;
        }
        .open-btn:hover { background: #1d4ed8; }
        .bank-notes {
            color: #64748b;
            font-size: 0.85rem;
            font-style: italic;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #eee;
        }
        .method-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 0.75rem;
            margin-right: 5px;
        }
        .method-badge.static { background: #dcfce7; color: #166534; }
        .method-badge.selenium { background: #fef3c7; color: #92400e; }
        .method-badge.api { background: #dbeafe; color: #1e40af; }
        .verified-date { color: #94a3b8; font-size: 0.75rem; }
        .open-all-btn {
            background: #10b981;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
            margin-left: auto;
        }
        .open-all-btn:hover { background: #059669; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Revision Manual de URLs - CDT Colombia</h1>
        <p class="subtitle">Herramienta para verificar manualmente las URLs de los bancos</p>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="total-banks">0</div>
                <div class="stat-label">Bancos Totales</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-urls">0</div>
                <div class="stat-label">URLs Totales</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="easy-count">0</div>
                <div class="stat-label">Facil Scraping</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="hard-count">0</div>
                <div class="stat-label">Requiere Selenium</div>
            </div>
        </div>

        <div class="filters">
            <div>
                <label>Filtrar por dificultad:</label>
                <select id="filter-difficulty" onchange="filterBanks()">
                    <option value="all">Todos</option>
                    <option value="easy">Facil</option>
                    <option value="medium">Medio</option>
                    <option value="hard">Dificil</option>
                </select>
            </div>
            <div>
                <label>Filtrar por metodo:</label>
                <select id="filter-method" onchange="filterBanks()">
                    <option value="all">Todos</option>
                    <option value="static">Estatico</option>
                    <option value="selenium">Selenium</option>
                    <option value="api">API</option>
                </select>
            </div>
            <div>
                <label>Buscar:</label>
                <input type="text" id="search" placeholder="Nombre del banco..." oninput="filterBanks()">
            </div>
            <button class="open-all-btn" onclick="openAllFiltered()">Abrir URLs Filtradas</button>
        </div>

        <div class="banks-grid" id="banks-grid">
        </div>
    </div>

    <script>
        const banksData = ''' + json.dumps(VERIFIED_BANK_URLS, ensure_ascii=False) + ''';

        function renderBanks(banks) {
            const grid = document.getElementById('banks-grid');
            grid.innerHTML = '';

            Object.entries(banks).forEach(([code, bank]) => {
                const urlsHtml = Object.entries(bank.urls).map(([type, url]) => `
                    <div class="url-item">
                        <span class="url-type">${type}</span>
                        <a href="${url}" target="_blank" class="url-link">${url}</a>
                        <button class="open-btn" onclick="window.open('${url}', '_blank')">Abrir</button>
                    </div>
                `).join('');

                const card = `
                    <div class="bank-card" data-code="${code}" data-difficulty="${bank.difficulty}" data-method="${bank.scraping_method}">
                        <div class="bank-header">
                            <div>
                                <div class="bank-name">${bank.name}</div>
                                <div class="bank-code">${code}</div>
                            </div>
                            <span class="difficulty ${bank.difficulty}">${bank.difficulty}</span>
                        </div>
                        <div>
                            <span class="method-badge ${bank.scraping_method}">${bank.scraping_method}</span>
                            <span class="verified-date">Verificado: ${bank.last_verified}</span>
                        </div>
                        <div class="urls-list">
                            ${urlsHtml}
                        </div>
                        <div class="bank-notes">${bank.notes}</div>
                    </div>
                `;
                grid.innerHTML += card;
            });
        }

        function filterBanks() {
            const difficulty = document.getElementById('filter-difficulty').value;
            const method = document.getElementById('filter-method').value;
            const search = document.getElementById('search').value.toLowerCase();

            const filtered = {};
            Object.entries(banksData).forEach(([code, bank]) => {
                const matchesDifficulty = difficulty === 'all' || bank.difficulty === difficulty;
                const matchesMethod = method === 'all' || bank.scraping_method === method;
                const matchesSearch = bank.name.toLowerCase().includes(search) || code.toLowerCase().includes(search);

                if (matchesDifficulty && matchesMethod && matchesSearch) {
                    filtered[code] = bank;
                }
            });

            renderBanks(filtered);
        }

        function openAllFiltered() {
            const cards = document.querySelectorAll('.bank-card');
            cards.forEach(card => {
                const links = card.querySelectorAll('.url-link');
                links.forEach((link, index) => {
                    setTimeout(() => window.open(link.href, '_blank'), index * 500);
                });
            });
        }

        function updateStats() {
            let totalUrls = 0;
            let easyCount = 0;
            let hardCount = 0;

            Object.values(banksData).forEach(bank => {
                totalUrls += Object.keys(bank.urls).length;
                if (bank.difficulty === 'easy') easyCount++;
                if (bank.difficulty === 'hard' || bank.scraping_method === 'selenium') hardCount++;
            });

            document.getElementById('total-banks').textContent = Object.keys(banksData).length;
            document.getElementById('total-urls').textContent = totalUrls;
            document.getElementById('easy-count').textContent = easyCount;
            document.getElementById('hard-count').textContent = hardCount;
        }

        // Inicializar
        renderBanks(banksData);
        updateStats();
    </script>
</body>
</html>'''
    return html


def save_review_page(output_dir: str = None) -> str:
    """Guarda la pagina de revision"""
    if output_dir is None:
        output_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    html_path = os.path.join(output_dir, 'review.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(generate_review_html())

    return html_path


def open_review_page():
    """Abre la pagina de revision en el navegador"""
    html_path = save_review_page()
    webbrowser.open(f'file://{html_path}')
    print(f"Pagina de revision abierta: {html_path}")


def export_urls_json(output_path: str = None) -> str:
    """Exporta las URLs verificadas a JSON"""
    if output_path is None:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'verified_urls.json')

    export_data = {
        'exported_at': datetime.now().isoformat(),
        'total_banks': len(VERIFIED_BANK_URLS),
        'banks': VERIFIED_BANK_URLS
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    return output_path


def main():
    """Funcion principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Herramienta de revision manual de URLs')
    parser.add_argument(
        'command',
        choices=['open', 'export', 'list'],
        help='Comando: open (abrir pagina), export (exportar JSON), list (listar URLs)'
    )

    args = parser.parse_args()

    if args.command == 'open':
        open_review_page()
    elif args.command == 'export':
        path = export_urls_json()
        print(f"URLs exportadas a: {path}")
    elif args.command == 'list':
        print("\n" + "=" * 70)
        print("URLs VERIFICADAS DE BANCOS - CDT COLOMBIA")
        print("=" * 70)
        for code, bank in sorted(VERIFIED_BANK_URLS.items()):
            print(f"\n{bank['name']} ({code})")
            print(f"  Dificultad: {bank['difficulty']} | Metodo: {bank['scraping_method']}")
            for url_type, url in bank['urls'].items():
                print(f"  [{url_type}] {url}")
        print("=" * 70)


if __name__ == '__main__':
    main()
