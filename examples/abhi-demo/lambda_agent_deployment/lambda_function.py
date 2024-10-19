import json
import urllib.request
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
        raise e

    secret: str = secret_value["SecretString"]

    return secret


OPENWEATHERMAP_API_KEY = get_from_secretstore_or_env("GEOCODING_API_KEY")

def lambda_handler(event, context):
    # Get the city name from the event payload
    city_name = event['city']

    # Get the location coordinates using OpenWeatherMap API
    openweathermap_url = f'http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHERMAP_API_KEY}'
    try:
        response = urllib.request.urlopen(openweathermap_url)
        data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {
            'statusCode': e.code,
            'body': json.dumps({
                'error': f'Failed to get location coordinates for {city_name}'
            })
        }

    lat = data['coord']['lat']
    lon = data['coord']['lon']

    # Get the weather conditions using Open-Meteo API
    open_meteo_url = f'{OPEN_METEO_BASE_URL}?latitude={lat}&longitude={lon}&current_weather=true'
    try:
        response = urllib.request.urlopen(open_meteo_url)
        data = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {
            'statusCode': e.code,
            'body': json.dumps({
                'error': 'Failed to get weather conditions'
            })
        }

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