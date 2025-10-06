import requests
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import math

#API
NASA_API_KEY = "XAGC8IHl7BEtkaJ0UcPhAQhQmKEoQGZMxPev0Z1y"

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
def simulate_hourly_temps(min_temp, max_temp):
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

def get_nasa_historical_weather_for_date(lat, lon, target_date):
    date_str = target_date.strftime("%Y%m%d")
    base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = { "parameters": "T2M_MAX,T2M_MIN,PRECTOTCORR,WS10M", "community": "AG", "longitude": lon, "latitude": lat, "start": date_str, "end": date_str, "format": "JSON", "api_key": NASA_API_KEY }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()['properties']['parameter']
        max_temp = data.get('T2M_MAX', {}).get(date_str, -999)
        min_temp = data.get('T2M_MIN', {}).get(date_str, -999)
        precipitation = data.get('PRECTOTCORR', {}).get(date_str, -999)
        wind_speed = data.get('WS10M', {}).get(date_str, -999)
        if -999 in [max_temp, min_temp, precipitation, wind_speed]: return None
        rain_prob = min(100, int(20 + precipitation * 10)) if precipitation > 0.1 else 0
        return { "date": target_date.strftime("%Y-%m-%d"), "temp": round((max_temp + min_temp) / 2, 1), "min": round(min_temp, 1), "max": round(max_temp, 1), "rain": round(precipitation, 1), "rainProb": rain_prob, "wind": round(wind_speed, 1), "hourly_data": simulate_hourly_temps(min_temp, max_temp) }
    except (requests.exceptions.RequestException, KeyError) as e:
        print(f"Error processing NASA data for {date_str}: {e}")
        return None

def generate_recommendations(summary):
    recs = []
    if summary['max'] > 28 and summary['rainProb'] > 40: recs.append("🥵💧 Heat and rain history. Consider light, waterproof clothing and stay well hydrated.")
    elif summary['min'] < 10 and summary['rainProb'] > 40: recs.append("🥶💧 History of cold and rain. Dress in layers with a good waterproof coat.")
    is_rain_mentioned = any("rain" in rec.lower() for rec in recs)
    if not is_rain_mentioned:
        if summary['rainProb'] > 60: recs.append("☔ High probability of historic rainfall. Don't forget your umbrella!")
        elif summary['rainProb'] > 30: recs.append("🌦️ History of scattered rainfall. It would be a good idea to bring a raincoat.")
    is_temp_mentioned = any("heat" in rec.lower() or "cold" in rec.lower() for rec in recs)
    if not is_temp_mentioned:
        if summary['max'] > 30: recs.append("🥵 Historically very hot day. Seek shade and use sunscreen.")
        elif summary['min'] < 10: recs.append("🥶 Historically cold day. Be sure to bundle up!")
    if summary['wind'] > 25:
        if recs and "cold" in recs[-1]: recs[-1] += " Strong winds could make it feel colder."
        else: recs.append("💨 Historically strong winds. Be careful with loose objects.")
    if not recs: recs.append("👍 The weather at this time of year is usually pleasant, with no notable extreme conditions.")
    return recs

@app.get("/weather")
async def get_weather_data(lat: float, lon: float, day: int, month: int, year: int):
    historical_yearly_data = []
    for i in range(1, 6):
        target_year = year - i
        try:
            target_date = datetime(target_year, month, day)
            weather_report = get_nasa_historical_weather_for_date(lat, lon, target_date)
            if weather_report: historical_yearly_data.append(weather_report)
        except ValueError: continue
    if not historical_yearly_data: return {"error": "Historical data could not be obtained."}
    summary = { "temp": round(sum(d['temp'] for d in historical_yearly_data) / len(historical_yearly_data), 1), "min": round(sum(d['min'] for d in historical_yearly_data) / len(historical_yearly_data), 1), "max": round(sum(d['max'] for d in historical_yearly_data) / len(historical_yearly_data), 1), "rain": round(sum(d['rain'] for d in historical_yearly_data) / len(historical_yearly_data), 1), "rainProb": int(sum(d['rainProb'] for d in historical_yearly_data) / len(historical_yearly_data)), "wind": int(sum(d['wind'] for d in historical_yearly_data) / len(historical_yearly_data)), "hourly_data": historical_yearly_data[0]['hourly_data'], }
    recommendations = generate_recommendations(summary)
    return { "historical_summary": summary, "historical_yearly_data": historical_yearly_data, "recommendations": recommendations }

@app.get("/forecast")
async def get_forecast_data(lat: float, lon: float, date: str):
    target_date = datetime.strptime(date, "%Y-%m-%d")
    today = datetime.now()

    if (target_date - today).days > 10:
        return {"status": "unavailable", "message": "Forecast not available for dates more than 10 days in advance."}

    is_past_date = target_date < today
    diff_days = (today - target_date).days if is_past_date else -1

    # Choose of API
    if is_past_date and diff_days > 90:
        base_url = "https://archive-api.open-meteo.com/v1/archive"
        end_date_str = date
        # Para fechas antiguas, pedimos 'precipitation_sum'
        daily_params_str = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum"
    else:
        base_url = "https://api.open-meteo.com/v1/forecast"
        end_date_str = (target_date + timedelta(days=4)).strftime("%Y-%m-%d")
        # Para fechas recientes, pedimos 'precipitation_probability_max'
        daily_params_str = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"

    params = {
        "latitude": lat, "longitude": lon,
        "daily": daily_params_str,
        "hourly": "temperature_2m,weather_code", "timezone": "auto", "start_date": date,
        "end_date": end_date_str
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        daily_data = data['daily']
        #Rain Prob.
        rain_prob = 0
        if "precipitation_probability_max" in daily_data:
            rain_prob = daily_data['precipitation_probability_max'][0]
        elif "precipitation_sum" in daily_data:
            precipitation_sum = daily_data['precipitation_sum'][0]
            if precipitation_sum is not None and precipitation_sum > 0.1:
                rain_prob = min(100, int(20 + precipitation_sum * 10))

        main_day_data = { "date": daily_data['time'][0], "max": daily_data['temperature_2m_max'][0], "min": daily_data['temperature_2m_min'][0], "rainProb": rain_prob, "weatherCode": daily_data['weather_code'][0], }
        
        forecast_days = []
        if len(daily_data['time']) > 1:
            for i in range(1, len(daily_data['time'])):
                 prob_forecast = daily_data['precipitation_probability_max'][i]
                 forecast_days.append({ "date": daily_data['time'][i], "max": daily_data['temperature_2m_max'][i], "min": daily_data['temperature_2m_min'][i], "rainProb": prob_forecast, "weatherCode": daily_data['weather_code'][i], })

        hourly_data_response = data['hourly']
        hourly_data = []
        for i in range(24): 
            hourly_data.append({ "hour": hourly_data_response['time'][i].split("T")[1], "temp": hourly_data_response['temperature_2m'][i] })
        
        return { "main_day": main_day_data, "forecast": forecast_days, "hourly_data": hourly_data }

    except requests.exceptions.RequestException as e:
        print(f"Error calling the Open-Meteo API: {e}")
        return {"error": "The weather forecast could not be obtained."}