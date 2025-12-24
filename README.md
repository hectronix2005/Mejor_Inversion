# InvierteColombia

Comparador inteligente de inversiones en Colombia. Compara tasas de CDTs, cuentas de ahorro de alto rendimiento, derechos fiduciarios y rendimientos de finca raíz.

## Ranking Actual (Diciembre 2024)

| Entidad | Tipo | 30 Días | 60 Días | 90 Días |
|---------|------|---------|---------|---------|
| Atomy Rent | Derechos Fiduciarios | 15.50% | 15.50% | 15.50% |
| Pibank | Cuenta Ahorro | 10.00% | 10.00% | 10.00% |
| Nubank | Cuenta Ahorro | 9.25% | 9.25% | 9.25% |
| Lulo Bank | Cuenta Ahorro | 9.00% | 9.00% | 9.00% |
| Bancolombia | CDT | 9.50% | 9.75% | 10.00% |
| Davivienda | CDT | 9.25% | 9.50% | 9.75% |
| BBVA Colombia | CDT | 9.00% | 9.25% | 9.50% |
| Banco de Bogotá | CDT | 8.75% | 9.00% | 9.25% |
| Scotiabank Colpatria | CDT | 8.50% | 8.75% | 9.00% |
| AV Villas | CDT | 8.25% | 8.50% | 8.75% |
| Finca Raíz Colombia | Finca Raíz | 6.00% | 6.50% | 7.00% |

## Tipos de Inversión

- **CDT**: Certificado de Depósito a Término - Inversión tradicional en bancos
- **Cuenta Ahorro**: Cuentas de ahorro de alto rendimiento (Neobancos)
- **Derechos Fiduciarios**: Inversión en activos inmobiliarios a través de fiducias
- **Finca Raíz**: Rendimiento estimado por arrendamiento de propiedades

## Instalación

```bash
# Clonar repositorio
git clone https://github.com/hectronix2005/Mejor_Inversion.git
cd Mejor_Inversion

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## Uso

### Iniciar la aplicación completa

```bash
python run.py
```

Esto inicia:
- API REST en `http://localhost:5001`
- Abre automáticamente la página web en el navegador

### Comandos CLI

```bash
# Solo ejecutar scraping
python run.py scrape

# Solo iniciar API
python run.py api

# Abrir página web
python run.py web
```

## API Endpoints

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/rates` | GET | Obtiene todas las tasas actuales |
| `/api/rates/<bank_code>` | GET | Tasas de un banco específico |
| `/api/banks` | GET | Lista de bancos configurados |
| `/api/compare` | GET | Comparación por plazo |
| `/api/scrape` | POST | Ejecuta scraping manual |
| `/health` | GET | Estado de la API |

### Ejemplos

```bash
# Obtener todas las tasas
curl http://localhost:5001/api/rates

# Comparar tasas a 90 días
curl "http://localhost:5001/api/compare?term=90"

# Ejecutar scraping
curl -X POST http://localhost:5001/api/scrape
```

## Estructura del Proyecto

```
MejorInversion/
├── index.html              # Frontend principal
├── run.py                  # Script de ejecución
├── requirements.txt        # Dependencias Python
├── scrapers/
│   ├── config.py          # Configuración de bancos
│   ├── base_scraper.py    # Clases base para scrapers
│   ├── bank_scrapers.py   # Scrapers individuales
│   └── orchestrator.py    # Orquestador de scraping
├── api/
│   └── app.py             # API REST Flask
└── data/
    ├── rates.json         # Tasas actuales
    └── history/           # Histórico de tasas
```

## Fuentes de Datos

- **CDTs**: Páginas oficiales de cada banco
- **Neobancos**: Información pública de Nubank, Pibank, Lulo Bank
- **Atomy Rent**: https://atomyrent.com/
- **Finca Raíz**: Datos de Fedelonjas (rendimiento arriendo 0.4%-0.6% mensual)

## Tecnologías

- **Backend**: Python 3, Flask, BeautifulSoup4
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Scraping**: Requests, Selenium (para sitios dinámicos)

## Disclaimer

Las tasas mostradas son referenciales y pueden variar. Consulte directamente con cada entidad financiera para obtener información actualizada y condiciones específicas. Este proyecto es solo con fines educativos e informativos.

## Licencia

MIT License
