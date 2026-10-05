
[![Python][python-shield]][python-url]
[![Flask][flask-shield]][flask-url]
[![Vue.js][Vue.js]][Vue-url]
[![Node.js][node-shield]][node-url]
[![npm][npm-shield]][npm-url]
[![License][license-shield]][license-url]

#  🌦 Pronostika 🌦

Pronostika is a web application that allows you to plan outdoor activities with confidence using personalized long-term weather forecasts. Users simply enter their destination and travel date, and the application returns a clear assessment of the likelihood of adverse conditions (e.g., “very rainy,” “very hot,” or “very windy”). Pronostika solves the problem of inaccessibility of extended weather forecasts: we transform complex terrestrial observation data and historical NASA records into useful information for the user, going beyond the usual short-term forecasts. In other words, by processing advanced satellite data and historical climate data, Pronostika helps travelers, hikers, and event organizers make informed decisions weeks or months in advance. In this way, our app improves the safety of outdoor travel, reduces the risk of plans being ruined by the weather, and allows for better preparation. By connecting satellite data with users' everyday needs, Pronostika promotes safer and more enjoyable outdoor adventures for everyone.

## Project Demonstration

![demo](https://github.com/user-attachments/assets/6d456094-5761-411b-92dc-d83f878939b7)

## Technical Details of the Project

The solution follows a modern client-server architecture. The frontend is developed in Vue.js for the interactive interface, and the backend is an API written in Python (for example, using Flask or FastAPI). The backend handles all the processing: it obtains meteorological data (e.g., from NASA APIs), manipulates it with libraries such as **Pandas** and **NumPy**, and runs prediction models. It then exposes a REST API that the frontend consumes to display the results. For example, the typical data flow is: the frontend sends latitude, longitude, and date to the backend, which obtains historical data (precipitation, temperature, wind, etc.), runs the forecast model, and returns the probability of extreme conditions. The frontend receives these probabilities and displays maps or graphs indicating areas at risk of “very rainy,” “very hot,” etc.

In terms of data processing, we collect several years of precipitation and climate data (e.g., from GPM and other satellites) and use it to train our models. We define typical weather thresholds to classify extreme conditions: for example, **“very rainy”** when precipitation exceeds 50 mm in 24 hours, **“very hot”** when the temperature exceeds 35°C, and **“very windy”** when gusts exceed 15 m/s. These criteria are based on climate data and common meteorological practices. The system periodically validates these definitions with real information to adjust the thresholds. In summary, data flows from external sources to our AI model in the backend, and back to the user through the frontend.

## Data Sources and APIs

Pronostika draws on various meteorological and environmental data sources from space agencies and scientific institutions:

- **NASA POWER API**: provides global historical climate data (temperatures, precipitation, etc.) ready for analysis.
- **NASA Global Precipitation Measurement (GPM) Mission**: provides highly accurate global precipitation measurements. This mission also improves forecast models by integrating satellite data, making predictions more accurate.
- **Partner Agencies (CNES, ISRO, NOAA, EUMETSAT)**: GPM is an international collaboration that includes CNES (France), ISRO (India), NOAA (USA), and EUMETSAT (Europe). Thanks to these partners, we have global coverage of climate data.
- **Other meteorological data**: We can incorporate data from NOAA, ECMWF, or ground-based observatories as needed. For example, if necessary, we would use the **NASA FIRMS** database to monitor related environmental conditions or NOAA's historical climate database.
- **Project repository**: Pronostika's source code is available on GitHub: [github.com/SuitPumpkin/Will-It-Rain-On-My-Parade](https://github.com/SuitPumpkin/Will-It-Rain-On-My-Parade). The implementation details are documented there, and the backend and frontend code is hosted there.

## Technologies and Tools

Pronostika was built using a set of mature and popular technologies: - **Python 3.x** - for the backend, data processing, and statistical modeling (libraries: pandas, numpy, requests).  
\- **Flask / FastAPI** - lightweight Python framework for exposing the backend API.  
\- **Vue.js** - JavaScript framework for the frontend (interactive interface and visualizations).  
\- **TensorFlow/Keras** and **scikit-learn** - for training and running machine learning models (LSTM, ARIMA, etc.).  
\- **REST APIs** - we consume external APIs (NASA POWER, GPM) using HTTP calls from the backend.  
\- **Node.js, npm** - to manage dependencies and run the Vue application.  
\- **Visualization libraries** - (e.g., Chart.js or D3.js) to graph data on the frontend.  
\- **Version control** - Git/GitHub for the source code.

## Installation and Configuration

To run Pronostika locally, follow these steps:

- **Clone the repository:**

- git clone <https://github.com/SuitPumpkin/Will-It-Rain-On-My-Parade.git>

- **Install dependencies (backend):**
- Navigate to the backend directory:

- cd Will-It-Rain-On-My-Parade/backend

- (Optional) Create a Python virtual environment and activate it:  

- python -m venv venv  
    source venv/bin/activate # Windows: venv\\Scripts\\activate

- Install the necessary libraries:  

- pip install -r requirements.txt

- **Configure the backend environment:**
- Create a `backend/.env` file based on `backend/.env.example` and add your NASA API key:

```env
NASA_API_KEY=your_nasa_api_key
```

- When deploying on Render, configure `NASA_API_KEY` as an environment variable in the backend service settings. Do not commit the `.env` file.

- Configure the backend allowed frontend origins with `CORS_ORIGINS`, using comma-separated URLs:

```env
CORS_ORIGINS=http://localhost:8080,http://localhost:5173
```

- For the frontend, copy `frontend/.env.example` to `frontend/.env.local` for local development. On Render, set `VUE_APP_API_URL` to the public URL of the backend service.

- **Install dependencies (frontend):**
- Go to the frontend directory:

- cd ../frontend

- Install Node.js packages:

- npm install

- **Run the application:**
- Start the backend (e.g., python app.py or the command defined in the repository).
- Start the frontend server:

- npm run serve

- Open your browser at <http://localhost:8080> (or the specified port) to use Pronostika.
- **Additional configuration:**
- Pronostika uses the NASA POWER API. The backend requires the `NASA_API_KEY` environment variable to be configured before it starts.
- If desired, adjust parameters in the code (e.g., “very rainy” thresholds) within the backend configuration files.

## Deployment on Render

Create a **Web Service** for `backend` with:

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`
- Environment variables: `NASA_API_KEY` and `CORS_ORIGINS`

Create a **Static Site** for `frontend` with:

- Root directory: `frontend`
- Build command: `npm ci && npm run build`
- Publish directory: `dist`
- Environment variable: `VUE_APP_API_URL=https://<backend-service>.onrender.com`

After the frontend is deployed, update the backend's `CORS_ORIGINS` to its exact public URL, for example `https://<frontend-site>.onrender.com`. Multiple origins can be separated by commas.

With these steps, you will have a local copy of the application up and running. The structure is independent of external services (we do not rely on third-party databases) and can be tested without additional keys.

## Use

Once the application is installed, it is easy to use:  
\- Open the web interface (e.g., <http://localhost:8080>).  
\- Enter the **destination location** (either by coordinates or city name, depending on the implementation) and the desired **travel date**.  
\- Press the **Predict weather** button or equivalent. Pronostika will consult its internal models and immediately display the probability of adverse conditions such as heavy rain, extreme heat, or strong winds.  
\- The result is presented graphically: for example, with probability bars, heat maps in the selected region, and clear messages (“There is a 70% chance of heavy rain”). This way, you can easily interpret whether it is worth rescheduling or preparing special equipment (umbrella, sunscreen, etc.).  
\- For more technical details or use cases, see the documentation (link to the code README or Wiki if available).

## License

This project is distributed under the **MIT** license. See the LICENSE file for details.

## Contact

Tamales.bat Team - NASA Space Apps Challenge 2025.  
Project repository: [github.com/SuitPumpkin/Will-It-Rain-On-My-Parade](https://github.com/SuitPumpkin/Will-It-Rain-On-My-Parade).

## Acknowledgments

We would like to thank the following resources and communities that made this project possible:  
\- [NASA POWER API](https://power.larc.nasa.gov): source of global meteorological data.  
\- [NASA GPM Mission](https://gpm.nasa.gov): global satellite precipitation data.  
\- [NASA Earth Observations (NEO)](https://neo.sci.gsfc.nasa.gov): environmental images and data.  
\- [NASA Space Apps Challenge](https://www.spaceappschallenge.org): global challenge platform where this idea originated.  
\- [Vue.js](https://vuejs.org) and [Flask](https://flask.palletsprojects.com): frameworks for the frontend and backend.

Thank you to all contributors and users for your support and ongoing feedback.

<!-- MARKDOWN LINKS & IMAGES -->
[python-shield]: https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge&logo=python&logoColor=white
[python-url]: https://www.python.org/
[flask-shield]: https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white
[flask-url]: https://flask.palletsprojects.com/
[Vue.js]: https://img.shields.io/badge/Vue.js-35495E?style=for-the-badge&logo=vuedotjs&logoColor=4FC08D
[Vue-url]: https://vuejs.org/
[node-shield]: https://img.shields.io/badge/Node.js-43853D?style=for-the-badge&logo=nodedotjs&logoColor=white
[node-url]: https://nodejs.org/
[npm-shield]: https://img.shields.io/badge/npm-CB3837?style=for-the-badge&logo=npm&logoColor=white
[npm-url]: https://www.npmjs.com/
[license-shield]: https://img.shields.io/badge/License-MIT-yellow.svg

[license-url]: https://opensource.org/licenses/MIT
