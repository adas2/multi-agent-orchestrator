import json
import requests
import boto3

# OPENWEATHERMAP_API_KEY = 'YOUR_OPENWEATHERMAP_API_KEY'
OPEN_METEO_BASE_URL = 'https://api.open-meteo.com/v1/forecast'
# AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


def get_from_secretstore_or_env(key: str) -> str:

    session = boto3.session.Session()
    secrets_manager = session.client(service_name="secretsmanager", region_name="us-east-1")
    try:
        secret_value = secrets_manager.get_secret_value(SecretId=key)
    except Exception as e:
        # logger.error(f"could not get secret {key} from secrets manager: {e}")
        raise e

    secret: str = secret_value["SecretString"]

    return secret


OPENWEATHERMAP_API_KEY = get_from_secretstore_or_env("GEOCODING_API_KEY")

def lambda_handler(event, context):
    # Get the city name from the event payload
    city_name = event['city']

    # Get the location coordinates using OpenWeatherMap API
    openweathermap_url = f'http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHERMAP_API_KEY}'
    response = requests.get(openweathermap_url)
    
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': json.dumps({
                'error': f'Failed to get location coordinates for {city_name}'
            })
        }

    data = response.json()
    lat = data['coord']['lat']
    lon = data['coord']['lon']

    # Get the weather conditions using Open-Meteo API
    open_meteo_url = f'{OPEN_METEO_BASE_URL}?latitude={lat}&longitude={lon}&current_weather=true'
    response = requests.get(open_meteo_url)

    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'body': json.dumps({
                'error': 'Failed to get weather conditions'
            })
        }

    data = response.json()
    weather_conditions = data['current_weather']

    return {
        'statusCode': 200,
        'body': json.dumps({
            'location': {
                'city': city_name,
                'latitude': lat,
                'longitude': lon
            },
            'weather': weather_conditions
        })
    }