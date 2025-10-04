from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# USAREMOS WEATHERAPI.COM QUE FUNCIONÓ BIEN
# Asegúrate de poner tu clave de WeatherAPI.com aquí
API_KEY = 'a7bbc878e3864948929195140250410'
BASE_URL = 'http://api.weatherapi.com/v1/current.json'

@app.route('/clima', methods=['GET'])
def get_clima():
    # WeatherAPI puede buscar por coordenadas o por nombre.
    # Usemos coordenadas, que son más precisas.
    lat = request.args.get('lat')
    lon = request.args.get('lon')

    if not lat or not lon:
        return jsonify({'error': 'Los parámetros lat y lon son requeridos'}), 400

    # Creamos la cadena de consulta "latitud,longitud" que espera WeatherAPI
    query = f"{lat},{lon}"

    params = {
        'key': API_KEY,
        'q': query,
        'lang': 'es',
        'aqi': 'no'
    }

    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

        clima_info = {
            'ciudad': data['location']['name'],
            'temperatura': data['current']['temp_c'],
            'descripcion': data['current']['condition']['text'],
            'icono': data['current']['condition']['icon'].replace('//', 'https://'),
            'humedad': data['current']['humidity'],
            'sensacion_real': data['current']['feelslike_c']
        }
        
        return jsonify(clima_info)

    except requests.exceptions.HTTPError as err:
        return jsonify({'error': f"Error del servicio de clima: {err}"}), response.status_code
    except Exception as e:
        return jsonify({'error': f'Ocurrió un error en el servidor: {e}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)