"""
API REST para el sistema de CDTs
"""
import os
import json
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.orchestrator import CDTOrchestrator, run_scraping
from scrapers.config import DATA_DIR, RATES_FILE, STANDARD_TERMS

app = Flask(__name__, static_folder='../static')
CORS(app)

# Cache en memoria
_cached_data = None
_cache_time = None
CACHE_DURATION = 300  # 5 minutos


def get_rates_data():
    """Obtiene datos de tasas, del cache o archivo"""
    global _cached_data, _cache_time

    # Verificar cache en memoria
    if _cached_data and _cache_time:
        elapsed = (datetime.now() - _cache_time).total_seconds()
        if elapsed < CACHE_DURATION:
            return _cached_data

    # Cargar desde archivo
    if os.path.exists(RATES_FILE):
        with open(RATES_FILE, 'r', encoding='utf-8') as f:
            _cached_data = json.load(f)
            _cache_time = datetime.now()
            return _cached_data

    return None


@app.route('/')
def index():
    """Sirve la pagina principal"""
    return send_from_directory('..', 'index.html')


@app.route('/api/rates', methods=['GET'])
def get_rates():
    """
    Obtiene todas las tasas de CDT
    Query params:
    - term: filtrar por plazo (dias)
    - bank: filtrar por codigo de banco
    - min_rate: tasa minima
    - limit: numero maximo de resultados
    - sort: 'rate_desc' (default), 'rate_asc', 'term_asc', 'term_desc'
    """
    data = get_rates_data()
    if not data:
        return jsonify({'error': 'No hay datos disponibles'}), 404

    rates = data.get('all_rates', [])

    # Filtros
    term = request.args.get('term', type=int)
    bank = request.args.get('bank')
    min_rate = request.args.get('min_rate', type=float)
    limit = request.args.get('limit', type=int, default=100)
    sort = request.args.get('sort', default='rate_desc')

    if term:
        rates = [r for r in rates if r['term_days'] == term]

    if bank:
        rates = [r for r in rates if r['bank_code'] == bank]

    if min_rate:
        rates = [r for r in rates if r['rate_ea'] >= min_rate]

    # Ordenamiento
    if sort == 'rate_desc':
        rates.sort(key=lambda x: x['rate_ea'], reverse=True)
    elif sort == 'rate_asc':
        rates.sort(key=lambda x: x['rate_ea'])
    elif sort == 'term_asc':
        rates.sort(key=lambda x: x['term_days'])
    elif sort == 'term_desc':
        rates.sort(key=lambda x: x['term_days'], reverse=True)

    return jsonify({
        'success': True,
        'count': len(rates[:limit]),
        'total': len(rates),
        'rates': rates[:limit]
    })


@app.route('/api/ranking', methods=['GET'])
def get_ranking():
    """Obtiene el ranking completo de CDTs"""
    data = get_rates_data()
    if not data:
        return jsonify({'error': 'No hay datos disponibles'}), 404

    return jsonify({
        'success': True,
        'generated_at': data.get('generated_at'),
        'statistics': data.get('statistics'),
        'total_banks': data.get('total_banks'),
        'total_rates': data.get('total_rates'),
        'top_10': data.get('top_10', [])
    })


@app.route('/api/ranking/<int:term_days>', methods=['GET'])
def get_ranking_by_term(term_days):
    """Obtiene el ranking para un plazo especifico"""
    data = get_rates_data()
    if not data:
        return jsonify({'error': 'No hay datos disponibles'}), 404

    by_term = data.get('by_term', {})
    term_rates = by_term.get(str(term_days), [])

    return jsonify({
        'success': True,
        'term_days': term_days,
        'count': len(term_rates),
        'rates': term_rates
    })


@app.route('/api/banks', methods=['GET'])
def get_banks():
    """Obtiene lista de bancos disponibles"""
    data = get_rates_data()
    if not data:
        return jsonify({'error': 'No hay datos disponibles'}), 404

    rates = data.get('all_rates', [])
    banks = {}

    for rate in rates:
        code = rate['bank_code']
        if code not in banks:
            banks[code] = {
                'code': code,
                'name': rate['bank_name'],
                'min_rate': rate['rate_ea'],
                'max_rate': rate['rate_ea'],
                'terms_available': []
            }
        else:
            banks[code]['min_rate'] = min(banks[code]['min_rate'], rate['rate_ea'])
            banks[code]['max_rate'] = max(banks[code]['max_rate'], rate['rate_ea'])

        if rate['term_days'] not in banks[code]['terms_available']:
            banks[code]['terms_available'].append(rate['term_days'])

    # Ordenar por tasa maxima
    bank_list = sorted(banks.values(), key=lambda x: x['max_rate'], reverse=True)

    return jsonify({
        'success': True,
        'count': len(bank_list),
        'banks': bank_list
    })


@app.route('/api/bank/<bank_code>', methods=['GET'])
def get_bank_rates(bank_code):
    """Obtiene tasas de un banco especifico"""
    data = get_rates_data()
    if not data:
        return jsonify({'error': 'No hay datos disponibles'}), 404

    rates = data.get('all_rates', [])
    bank_rates = [r for r in rates if r['bank_code'] == bank_code]

    if not bank_rates:
        return jsonify({'error': f'Banco {bank_code} no encontrado'}), 404

    bank_rates.sort(key=lambda x: x['term_days'])

    return jsonify({
        'success': True,
        'bank_code': bank_code,
        'bank_name': bank_rates[0]['bank_name'],
        'count': len(bank_rates),
        'rates': bank_rates
    })


@app.route('/api/simulate', methods=['POST'])
def simulate_cdt():
    """
    Simula la ganancia de un CDT
    Body JSON:
    - amount: monto a invertir
    - term_days: plazo en dias
    - rate_ea: tasa efectiva anual (opcional, usa la mejor si no se especifica)
    - bank_code: codigo del banco (opcional)
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Se requiere JSON body'}), 400

    amount = data.get('amount')
    term_days = data.get('term_days')

    if not amount or not term_days:
        return jsonify({'error': 'Se requiere amount y term_days'}), 400

    # Obtener tasa
    rate_ea = data.get('rate_ea')
    bank_code = data.get('bank_code')

    if not rate_ea:
        rates_data = get_rates_data()
        if rates_data:
            all_rates = rates_data.get('all_rates', [])
            matching_rates = [r for r in all_rates if r['term_days'] == term_days]

            if bank_code:
                matching_rates = [r for r in matching_rates if r['bank_code'] == bank_code]

            if matching_rates:
                matching_rates.sort(key=lambda x: x['rate_ea'], reverse=True)
                rate_ea = matching_rates[0]['rate_ea']
            else:
                return jsonify({'error': 'No se encontro tasa para ese plazo'}), 404
        else:
            return jsonify({'error': 'No hay datos de tasas disponibles'}), 404

    # Calcular rendimiento
    rate_decimal = rate_ea / 100
    rate_period = ((1 + rate_decimal) ** (term_days / 365)) - 1
    gross_profit = amount * rate_period

    # Retencion en la fuente (4% sobre rendimientos financieros en Colombia)
    retention = gross_profit * 0.04
    net_profit = gross_profit - retention
    total = amount + net_profit

    return jsonify({
        'success': True,
        'input': {
            'amount': amount,
            'term_days': term_days,
            'rate_ea': rate_ea
        },
        'result': {
            'gross_profit': round(gross_profit, 2),
            'retention': round(retention, 2),
            'net_profit': round(net_profit, 2),
            'total': round(total, 2),
            'effective_rate': round(rate_period * 100, 4)
        }
    })


@app.route('/api/compare', methods=['POST'])
def compare_cdts():
    """
    Compara CDTs de diferentes bancos
    Body JSON:
    - amount: monto a invertir
    - term_days: plazo en dias
    - banks: lista de codigos de bancos (opcional, compara todos si no se especifica)
    """
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Se requiere JSON body'}), 400

    amount = data.get('amount', 10000000)
    term_days = data.get('term_days', 360)
    banks_filter = data.get('banks', [])

    rates_data = get_rates_data()
    if not rates_data:
        return jsonify({'error': 'No hay datos disponibles'}), 404

    all_rates = rates_data.get('all_rates', [])
    matching_rates = [r for r in all_rates if r['term_days'] == term_days]

    if banks_filter:
        matching_rates = [r for r in matching_rates if r['bank_code'] in banks_filter]

    # Calcular ganancia para cada banco
    comparisons = []
    for rate in matching_rates:
        rate_decimal = rate['rate_ea'] / 100
        rate_period = ((1 + rate_decimal) ** (term_days / 365)) - 1
        gross_profit = amount * rate_period
        retention = gross_profit * 0.04
        net_profit = gross_profit - retention

        comparisons.append({
            'bank_code': rate['bank_code'],
            'bank_name': rate['bank_name'],
            'rate_ea': rate['rate_ea'],
            'gross_profit': round(gross_profit, 2),
            'net_profit': round(net_profit, 2),
            'total': round(amount + net_profit, 2)
        })

    # Ordenar por ganancia neta
    comparisons.sort(key=lambda x: x['net_profit'], reverse=True)

    # Calcular diferencia con el mejor
    if comparisons:
        best_profit = comparisons[0]['net_profit']
        for c in comparisons:
            c['difference_from_best'] = round(best_profit - c['net_profit'], 2)

    return jsonify({
        'success': True,
        'input': {
            'amount': amount,
            'term_days': term_days
        },
        'count': len(comparisons),
        'comparisons': comparisons
    })


@app.route('/api/refresh', methods=['POST'])
def refresh_data():
    """Fuerza una actualizacion de los datos (ejecuta scraping)"""
    global _cached_data, _cache_time

    try:
        ranking = run_scraping()
        _cached_data = ranking
        _cache_time = datetime.now()

        return jsonify({
            'success': True,
            'message': 'Datos actualizados correctamente',
            'total_banks': ranking['total_banks'],
            'total_rates': ranking['total_rates'],
            'updated_at': ranking['generated_at']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/terms', methods=['GET'])
def get_available_terms():
    """Obtiene los plazos disponibles"""
    return jsonify({
        'success': True,
        'terms': STANDARD_TERMS,
        'terms_info': [
            {'days': 30, 'label': '1 mes'},
            {'days': 60, 'label': '2 meses'},
            {'days': 90, 'label': '3 meses'},
            {'days': 180, 'label': '6 meses'},
            {'days': 360, 'label': '1 ano'},
            {'days': 540, 'label': '18 meses'},
            {'days': 720, 'label': '2 anos'},
        ]
    })


@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Obtiene estadisticas generales del mercado"""
    data = get_rates_data()
    if not data:
        return jsonify({'error': 'No hay datos disponibles'}), 404

    stats = data.get('statistics', {})
    stats['generated_at'] = data.get('generated_at')
    stats['total_banks'] = data.get('total_banks')
    stats['total_rates'] = data.get('total_rates')

    # Agregar tendencia (comparar con historial si existe)
    stats['market_trend'] = 'estable'  # TODO: implementar comparacion historica

    return jsonify({
        'success': True,
        'statistics': stats
    })


def create_app():
    """Factory function para crear la app"""
    return app


if __name__ == '__main__':
    # Ejecutar scraping inicial si no hay datos
    if not os.path.exists(RATES_FILE):
        print("Ejecutando scraping inicial...")
        run_scraping()

    app.run(debug=True, host='0.0.0.0', port=5000)
