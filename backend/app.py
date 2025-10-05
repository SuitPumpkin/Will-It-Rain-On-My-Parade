import requests
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import math

# --- CONFIGURACIÓN ---
# ¡IMPORTANTE! Reemplaza "YOUR_API_KEY_HERE" con tu clave real de la API de la NASA.
NASA_API_KEY = "XAGC8IHl7BEtkaJ0UcPhAQhQmKEoQGZMxPev0Z1y"

# Inicializa la aplicación FastAPI
app = FastAPI()

# Configuración de CORS
origins = ["http://localhost:8080", "http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LÓGICA DE LA API DE LA NASA (Sin cambios) ---

def simulate_hourly_temps(min_temp: float, max_temp: float):
    if min_temp is None or max_temp is None or min_temp == -999 or max_temp == -999:
        return [{"hour": f"{i}:00", "temp": 0} for i in range(24)]
    
    hourly_temps = []
    amplitude = (max_temp - min_temp) / 2
    average_temp = min_temp + amplitude
    
    for i in range(24):
        radian = math.sin((i - 10) * (math.pi / 12))
        temp = round(average_temp + amplitude * radian, 1)
        hourly_temps.append({"hour": f"{i}:00", "temp": temp})
        
    return hourly_temps

def get_nasa_historical_weather_for_date(lat: float, lon: float, target_date: datetime):
    date_str = target_date.strftime("%Y%m%d")
    base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "T2M_MAX,T2M_MIN,PRECTOTCORR,WS10M",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": date_str,
        "end": date_str,
        "format": "JSON",
        "api_key": NASA_API_KEY
    }

    try:
        response = requests.get(base_url, params=params)
        print(f"-> URL consultada para NASA POWER: {response.url}")
        response.raise_for_status()
        data = response.json()

        if "properties" not in data or "parameter" not in data["properties"]:
            return None

        parsed_data = data['properties']['parameter']
        max_temp = parsed_data.get('T2M_MAX', {}).get(date_str, -999)
        min_temp = parsed_data.get('T2M_MIN', {}).get(date_str, -999)
        precipitation = parsed_data.get('PRECTOTCORR', {}).get(date_str, -999)
        wind_speed = parsed_data.get('WS10M', {}).get(date_str, -999)

        if -999 in [max_temp, min_temp, precipitation, wind_speed]:
             return None

        rain_prob = 0
        if precipitation > 0.1:
            rain_prob = min(100, int(20 + precipitation * 10))

        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "temp": round((max_temp + min_temp) / 2, 1),
            "min": round(min_temp, 1),
            "max": round(max_temp, 1),
            "rain": round(precipitation, 1),
            "rainProb": rain_prob,
            "wind": round(wind_speed, 1),
            "hourly_data": simulate_hourly_temps(min_temp, max_temp)
        }
    except (requests.exceptions.RequestException, KeyError) as e:
        print(f"Error procesando datos de NASA para {date_str}: {e}")
        return None

# --- FUNCIÓN DE RECOMENDACIONES MEJORADA ---
def generate_recommendations(summary: dict):
    """
    Genera recomendaciones detalladas y múltiples basadas en el resumen del clima.
    """
    recs = []
    
    # --- Combinaciones Específicas Primero ---
    # Caluroso y Lluvioso
    if summary['max'] > 28 and summary['rainProb'] > 40:
        recs.append("🥵💧 Historial de calor y lluvia. Considera ropa ligera e impermeable y mantente bien hidratado.")
    # Frío y Lluvioso
    elif summary['min'] < 10 and summary['rainProb'] > 40:
        recs.append("🥶💧 Historial de frío y lluvia. Viste por capas con un buen abrigo impermeable.")
    
    # --- Recomendaciones Individuales (se pueden sumar a las anteriores si no son contradictorias) ---
    
    # Lluvia (se añade si no se activó ya una combinación de lluvia)
    is_rain_mentioned = any("lluvia" in rec.lower() for rec in recs)
    if not is_rain_mentioned:
        if summary['rainProb'] > 60:
            recs.append("☔ Alta probabilidad de lluvia histórica. ¡No olvides el paraguas!")
        elif summary['rainProb'] > 30:
            recs.append("🌦️ Historial de lluvias dispersas. Sería bueno llevar un impermeable.")

    # Temperatura (se añade si no se activó ya una combinación de temperatura)
    is_temp_mentioned = any("calor" in rec.lower() or "frío" in rec.lower() for rec in recs)
    if not is_temp_mentioned:
        if summary['max'] > 30:
            recs.append("🥵 Día históricamente muy caluroso. Busca la sombra y usa protector solar.")
        elif summary['min'] < 10:
             recs.append("🥶 Día históricamente frío. ¡Asegúrate de abrigarte bien!")

    # Viento
    if summary['wind'] > 25:
        # Añade un consejo sobre el viento a una recomendación existente si es posible
        if recs and "frío" in recs[-1]:
            recs[-1] += " El viento fuerte podría aumentar la sensación de frío."
        else:
            recs.append("💨 Viento históricamente fuerte. Ten cuidado con objetos sueltos.")
    
    # Buen clima (solo si no hay otras alertas)
    if not recs and 20 <= summary['max'] <= 28 and summary['rainProb'] < 20:
        recs.append("☀️ El historial sugiere un día perfecto para actividades al aire libre. ¡Disfrútalo!")
    
    # Mensaje por defecto si no hay nada destacable
    if not recs:
        recs.append("👍 El clima para esta fecha suele ser agradable, sin condiciones extremas destacables.")
        
    return recs

@app.get("/weather")
async def get_weather_data(lat: float, lon: float, day: int, month: int):
    # Esta función no necesita cambios
    current_year = datetime.now().year
    
    historical_yearly_data = []
    for i in range(1, 6):
        year = current_year - i
        try:
            target_date = datetime(year, month, day)
            weather_report = get_nasa_historical_weather_for_date(lat, lon, target_date)
            if weather_report:
                historical_yearly_data.append(weather_report)
        except ValueError:
            continue

    if not historical_yearly_data:
        return {"error": "No se pudieron obtener datos históricos para la fecha y ubicación seleccionadas."}

    summary = {
        "temp": round(sum(d['temp'] for d in historical_yearly_data) / len(historical_yearly_data), 1),
        "min": round(sum(d['min'] for d in historical_yearly_data) / len(historical_yearly_data), 1),
        "max": round(sum(d['max'] for d in historical_yearly_data) / len(historical_yearly_data), 1),
        "rain": round(sum(d['rain'] for d in historical_yearly_data) / len(historical_yearly_data), 1),
        "rainProb": int(sum(d['rainProb'] for d in historical_yearly_data) / len(historical_yearly_data)),
        "wind": int(sum(d['wind'] for d in historical_yearly_data) / len(historical_yearly_data)),
        "hourly_data": historical_yearly_data[0]['hourly_data'],
    }
    
    recommendations = generate_recommendations(summary)

    return {
        "historical_summary": summary,
        "historical_yearly_data": historical_yearly_data,
        "recommendations": recommendations,
        "nearby_locations": [],
    }

