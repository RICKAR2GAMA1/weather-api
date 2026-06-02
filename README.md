# Weather API REST - Flask

API REST en Flask que consume OpenWeather API para obtener información del clima.

## Características

✅ Endpoints: `/health`, `/`, `/weather`, `/weather/multiple`  
✅ Soporte por ciudad o coordenadas (lat/lon)  
✅ Validaciones completas de parámetros  
✅ Manejo robusto de errores (401, 404, timeout, conexión)  
✅ Respuestas JSON limpias y estructuradas  
✅ Timeout de solicitudes configurado  

## Requisitos

- Python 3.7+
- Flask 3.0.0
- requests 2.31.0
- python-dotenv 1.0.0

## Instalación

1. **Clonar o descargar el proyecto**
```bash
cd weather-api
```

2. **Crear entorno virtual (recomendado)**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar API Key**
   - Ve a [OpenWeather API](https://openweathermap.org/api)
   - Crea una cuenta gratuita y obtén tu API key
   - Abre `.env` y reemplaza `tu_api_key_aqui` con tu API key

```env
OPENWEATHER_API_KEY=tu_api_key_aqui
```

5. **Ejecutar la aplicación**
```bash
python app.py
```

La API estará disponible en `http://localhost:5000`

## Endpoints

### 1. GET /health
Verifica que la API esté funcionando.

**Respuesta exitosa (200):**
```json
{
  "status": "healthy",
  "service": "Weather API",
  "timestamp": "2026-06-02T10:30:45.123456"
}
```

### 2. GET /
Información sobre la API y endpoints disponibles.

**Respuesta (200):**
```json
{
  "service": "Weather API REST",
  "version": "1.0.0",
  "description": "API que consume OpenWeather para obtener información del clima",
  "endpoints": {
    "GET /health": "Verifica que la API esté funcionando",
    "GET /": "Información sobre la API",
    "GET /weather": "Obtiene clima por ciudad o coordenadas",
    "POST /weather/multiple": "Obtiene clima de múltiples ciudades"
  }
}
```

### 3. GET /weather
Obtiene información del clima por ciudad o coordenadas.

**Parámetros query:**
- `city` (string): Nombre de la ciudad (ej: Madrid, Barcelona)
- `lat` (float): Latitud (ej: 40.4168)
- `lon` (float): Longitud (ej: -3.7038)

> ⚠️ Proporciona `city` O ambos `lat` y `lon`, no ambos tipos simultáneamente.

**Ejemplos:**

Por ciudad:
```bash
curl "http://localhost:5000/weather?city=Madrid"
```

Por coordenadas:
```bash
curl "http://localhost:5000/weather?lat=40.4168&lon=-3.7038"
```

**Respuesta exitosa (200):**
```json
{
  "success": true,
  "data": {
    "city": "Madrid",
    "country": "ES",
    "coordinates": {
      "latitude": 40.4168,
      "longitude": -3.7038
    },
    "weather": {
      "main": "Clear",
      "description": "cielo despejado",
      "icon": "01d"
    },
    "temperature": {
      "current": 28.5,
      "feels_like": 27.8,
      "min": 22.1,
      "max": 29.3
    },
    "humidity": 45,
    "pressure": 1013,
    "wind_speed": 3.2,
    "clouds": 10,
    "timestamp": "2026-06-02T10:30:45"
  }
}
```

**Errores posibles:**

- 400: Parámetros faltantes o conflictivos
- 401: API key inválida
- 404: Ciudad no encontrada
- 429: Límite de solicitudes excedido
- 504: Timeout (solicitud tardó demasiado)
- 503: Servicio no disponible

### 4. POST /weather/multiple
Obtiene información del clima para múltiples ciudades o coordenadas.

**Body JSON - Opción 1 (ciudades):**
```json
{
  "cities": ["Madrid", "Barcelona", "Valencia", "Bilbao"]
}
```

**Body JSON - Opción 2 (coordenadas):**
```json
{
  "coordinates": [
    {"lat": 40.4168, "lon": -3.7038},
    {"lat": 41.3874, "lon": 2.1686},
    {"lat": 39.4699, "lon": -0.3763}
  ]
}
```

**Ejemplos con curl:**

Por ciudades:
```bash
curl -X POST http://localhost:5000/weather/multiple \
  -H "Content-Type: application/json" \
  -d '{"cities": ["Madrid", "Barcelona"]}'
```

Por coordenadas:
```bash
curl -X POST http://localhost:5000/weather/multiple \
  -H "Content-Type: application/json" \
  -d '{"coordinates": [{"lat": 40.4168, "lon": -3.7038}, {"lat": 41.3874, "lon": 2.1686}]}'
```

**Respuesta exitosa (200 o 207 si hay parciales):**
```json
{
  "success": true,
  "summary": {
    "total": 3,
    "successful": 2,
    "failed": 1
  },
  "results": {
    "successful": [
      {
        "query": "Madrid",
        "data": {
          "city": "Madrid",
          "country": "ES",
          "coordinates": {...},
          "weather": {...},
          "temperature": {...},
          "humidity": 45,
          "pressure": 1013,
          "wind_speed": 3.2,
          "clouds": 10,
          "timestamp": "2026-06-02T10:30:45"
        }
      },
      {
        "query": "Barcelona",
        "data": {...}
      }
    ],
    "failed": [
      {
        "query": "CiudadInexistente",
        "error": "Ciudad no encontrada",
        "status_code": 404
      }
    ]
  }
}
```

## Códigos de Estado HTTP

| Código | Significado |
|--------|------------|
| 200 | Éxito - Solicitud completada correctamente |
| 207 | Éxito parcial - Algunas solicitudes fallaron en `/weather/multiple` |
| 400 | Bad Request - Parámetros faltantes o inválidos |
| 401 | Unauthorized - API key inválida |
| 404 | Not Found - Ciudad o ruta no encontrada |
| 429 | Too Many Requests - Límite de solicitudes excedido |
| 500 | Internal Server Error - Error en la aplicación |
| 503 | Service Unavailable - Servicio de OpenWeather no disponible |
| 504 | Gateway Timeout - Solicitud tardó demasiado (timeout) |

## Validaciones Implementadas

✅ **Parámetros de entrada:**
- Validación de campos requeridos
- Prevención de parámetros conflictivos
- Validación de tipos de datos
- Rango de coordenadas (lat -90 a 90, lon -180 a 180)

✅ **Manejo de errores:**
- Timeout (5 segundos configurables)
- Errores de conexión
- Errores de OpenWeather API
- JSON inválido

✅ **Respuestas:**
- Estructura consistente
- Mensajes de error descriptivos
- Timestamp en ISO format

## Ejemplos Completos

### Obtener clima de Madrid
```bash
curl "http://localhost:5000/weather?city=Madrid"
```

### Obtener clima por coordenadas (Eiffel Tower, París)
```bash
curl "http://localhost:5000/weather?lat=48.858&lon=2.2945"
```

### Obtener clima de varias ciudades
```bash
curl -X POST http://localhost:5000/weather/multiple \
  -H "Content-Type: application/json" \
  -d '{
    "cities": ["London", "Tokyo", "Sydney", "New York"]
  }'
```

## Notas Importantes

- La API key se carga desde el archivo `.env`
- El timeout de solicitud está configurado a 5 segundos
- Las temperaturas se devuelven en Celsius (métrica)
- Las coordenadas deben estar en rango válido (lat: -90 a 90, lon: -180 a 180)
- En `/weather/multiple`, los resultados exitosos se devuelven aunque haya errores parciales

## Troubleshooting

**Error: "OPENWEATHER_API_KEY no está configurada"**
- Verifica que exista el archivo `.env`
- Asegúrate de que contiene `OPENWEATHER_API_KEY` con tu clave

**Error: "API key inválida o no autorizada" (401)**
- Verifica que tu API key es correcta
- Comprueba que la cuenta está verificada en OpenWeather

**Error: "Ciudad no encontrada" (404)**
- Verifica la ortografía del nombre de la ciudad
- Intenta con nombres en inglés

**Error: Timeout (504)**
- Verifica tu conexión a internet
- OpenWeather API puede estar lenta, intenta de nuevo

## Licencia

MIT
