import os
from flask import Flask, jsonify, request
import requests
from dotenv import load_dotenv
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Configuración
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY')
OPENWEATHER_BASE_URL = 'https://api.openweathermap.org/data/2.5/weather'
TIMEOUT_SECONDS = 5

# Validación de API key al iniciar
if not OPENWEATHER_API_KEY:
    raise ValueError("OPENWEATHER_API_KEY no está configurada en .env")


def format_weather_response(data):
    """Formatea la respuesta de OpenWeather a un formato limpio"""
    return {
        'city': data.get('name'),
        'country': data.get('sys', {}).get('country'),
        'coordinates': {
            'latitude': data.get('coord', {}).get('lat'),
            'longitude': data.get('coord', {}).get('lon')
        },
        'weather': {
            'main': data.get('weather', [{}])[0].get('main'),
            'description': data.get('weather', [{}])[0].get('description'),
            'icon': data.get('weather', [{}])[0].get('icon')
        },
        'temperature': {
            'current': data.get('main', {}).get('temp'),
            'feels_like': data.get('main', {}).get('feels_like'),
            'min': data.get('main', {}).get('temp_min'),
            'max': data.get('main', {}).get('temp_max')
        },
        'humidity': data.get('main', {}).get('humidity'),
        'pressure': data.get('main', {}).get('pressure'),
        'wind_speed': data.get('wind', {}).get('speed'),
        'clouds': data.get('clouds', {}).get('all'),
        'timestamp': datetime.fromtimestamp(data.get('dt')).isoformat()
    }


def get_weather_data(city=None, lat=None, lon=None):
    """
    Obtiene datos de clima de OpenWeather API
    Retorna: tupla (datos, status_code, error_message)
    """
    params = {
        'appid': OPENWEATHER_API_KEY,
        'units': 'metric'  # Celsius
    }

    if city:
        params['q'] = city
    elif lat is not None and lon is not None:
        params['lat'] = lat
        params['lon'] = lon
    else:
        return None, 400, "Proporciona 'city' o 'lat' y 'lon'"

    try:
        response = requests.get(
            OPENWEATHER_BASE_URL,
            params=params,
            timeout=TIMEOUT_SECONDS
        )

        if response.status_code == 401:
            return None, 401, "API key inválida o no autorizada"
        elif response.status_code == 404:
            return None, 404, "Ciudad no encontrada"
        elif response.status_code == 429:
            return None, 429, "Límite de solicitudes excedido. Intenta más tarde"
        elif response.status_code == 500:
            return None, 503, "Servicio de OpenWeather no disponible"
        elif response.status_code != 200:
            return None, response.status_code, f"Error en OpenWeather API: {response.status_code}"

        return response.json(), 200, None

    except requests.exceptions.Timeout:
        return None, 504, f"Timeout: La solicitud tardó más de {TIMEOUT_SECONDS} segundos"
    except requests.exceptions.ConnectionError:
        return None, 503, "No hay conexión a internet o OpenWeather API no disponible"
    except requests.exceptions.RequestException as e:
        return None, 500, f"Error en la solicitud: {str(e)}"


@app.route('/health', methods=['GET'])
def health():
    """Verifica que la API esté funcionando"""
    return jsonify({
        'status': 'healthy',
        'service': 'Weather API',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/', methods=['GET'])
def index():
    """Información sobre la API"""
    return jsonify({
        'service': 'Weather API REST',
        'version': '1.0.0',
        'description': 'API que consume OpenWeather para obtener información del clima',
        'endpoints': {
            'GET /health': 'Verifica que la API esté funcionando',
            'GET /': 'Información sobre la API',
            'GET /weather': 'Obtiene clima por ciudad o coordenadas (parámetros: city o lat,lon)',
            'POST /weather/multiple': 'Obtiene clima de múltiples ciudades (JSON con lista: cities o coordinates)'
        }
    }), 200


@app.route('/weather', methods=['GET'])
def weather():
    """
    Obtiene información del clima
    Parámetros query:
    - city: nombre de la ciudad
    - lat, lon: latitud y longitud
    """
    city = request.args.get('city', '').strip()
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)

    # Validación: debe proporcionar city o ambos lat/lon
    if not city and (lat is None or lon is None):
        return jsonify({
            'error': 'Parámetros inválidos',
            'message': "Proporciona 'city' o ambos 'lat' y 'lon'",
            'example': '/weather?city=Madrid o /weather?lat=40.4168&lon=-3.7038'
        }), 400

    # Validación: no proporcionar ambos
    if city and (lat is not None or lon is not None):
        return jsonify({
            'error': 'Parámetros conflictivos',
            'message': "Proporciona solo 'city' o solo 'lat' y 'lon', no ambos"
        }), 400

    data, status_code, error = get_weather_data(city=city, lat=lat, lon=lon)

    if error:
        return jsonify({
            'error': error,
            'status_code': status_code
        }), status_code

    return jsonify({
        'success': True,
        'data': format_weather_response(data)
    }), 200


@app.route('/weather/multiple', methods=['POST'])
def weather_multiple():
    """
    Obtiene información del clima para múltiples ciudades
    Body JSON:
    {
        "cities": ["Madrid", "Barcelona", "Valencia"]
    }
    o
    {
        "coordinates": [
            {"lat": 40.4168, "lon": -3.7038},
            {"lat": 41.3874, "lon": 2.1686}
        ]
    }
    """
    try:
        data = request.get_json()
    except Exception:
        return jsonify({
            'error': 'JSON inválido',
            'message': 'El cuerpo de la solicitud debe ser JSON válido'
        }), 400

    if not data:
        return jsonify({
            'error': 'Cuerpo vacío',
            'message': 'Proporciona un JSON con "cities" o "coordinates"'
        }), 400

    cities = data.get('cities', [])
    coordinates = data.get('coordinates', [])

    # Validación
    if not cities and not coordinates:
        return jsonify({
            'error': 'Parámetros inválidos',
            'message': 'Proporciona "cities" (lista) o "coordinates" (lista de objetos con lat/lon)',
            'example_cities': {'cities': ['Madrid', 'Barcelona']},
            'example_coordinates': {'coordinates': [{'lat': 40.4168, 'lon': -3.7038}]}
        }), 400

    if cities and coordinates:
        return jsonify({
            'error': 'Parámetros conflictivos',
            'message': 'Proporciona solo "cities" o solo "coordinates", no ambos'
        }), 400

    results = {
        'successful': [],
        'failed': []
    }

    # Procesar ciudades
    if cities:
        if not isinstance(cities, list):
            return jsonify({
                'error': 'Tipo inválido',
                'message': '"cities" debe ser una lista de strings'
            }), 400

        for city in cities:
            if not isinstance(city, str) or not city.strip():
                results['failed'].append({
                    'query': city,
                    'error': 'Ciudad inválida: debe ser un string no vacío'
                })
                continue

            weather_data, status_code, error = get_weather_data(city=city.strip())
            if error:
                results['failed'].append({
                    'query': city.strip(),
                    'error': error,
                    'status_code': status_code
                })
            else:
                results['successful'].append({
                    'query': city.strip(),
                    'data': format_weather_response(weather_data)
                })

    # Procesar coordenadas
    if coordinates:
        if not isinstance(coordinates, list):
            return jsonify({
                'error': 'Tipo inválido',
                'message': '"coordinates" debe ser una lista de objetos'
            }), 400

        for i, coord in enumerate(coordinates):
            if not isinstance(coord, dict) or 'lat' not in coord or 'lon' not in coord:
                results['failed'].append({
                    'index': i,
                    'error': 'Objeto inválido: debe contener "lat" y "lon"'
                })
                continue

            try:
                lat = float(coord['lat'])
                lon = float(coord['lon'])

                # Validar rangos
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    raise ValueError("Coordenadas fuera de rango")

                weather_data, status_code, error = get_weather_data(lat=lat, lon=lon)
                if error:
                    results['failed'].append({
                        'query': f"lat={lat}, lon={lon}",
                        'error': error,
                        'status_code': status_code
                    })
                else:
                    results['successful'].append({
                        'query': f"lat={lat}, lon={lon}",
                        'data': format_weather_response(weather_data)
                    })

            except (ValueError, TypeError) as e:
                results['failed'].append({
                    'query': f"{coord}",
                    'error': f'Coordenadas inválidas: {str(e)}'
                })

    return jsonify({
        'success': len(results['failed']) == 0,
        'summary': {
            'total': len(cities) + len(coordinates),
            'successful': len(results['successful']),
            'failed': len(results['failed'])
        },
        'results': results
    }), 200 if results['successful'] else 207


@app.errorhandler(404)
def not_found(error):
    """Manejador para rutas no encontradas"""
    return jsonify({
        'error': 'No encontrado',
        'message': 'La ruta solicitada no existe',
        'available_endpoints': ['/health', '/', '/weather', '/weather/multiple']
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    """Manejador para métodos no permitidos"""
    return jsonify({
        'error': 'Método no permitido',
        'message': f"El método {request.method} no está permitido en esta ruta"
    }), 405


@app.errorhandler(500)
def internal_error(error):
    """Manejador para errores internos"""
    return jsonify({
        'error': 'Error interno del servidor',
        'message': 'Ocurrió un error inesperado'
    }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
