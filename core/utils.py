import requests
from django.conf import settings
def get_genre_mapping(media_type="movie"):
    genre_url = f"https://api.themoviedb.org/3/genre/{media_type}/list"
    params = {
        "api_key": settings.TMDB_API_KEY,
        "language": "en-US"
    }
    try:
        response = requests.get(genre_url, params=params)
        response.raise_for_status()
        data = response.json()
        return {genre['id']: genre['name'] for genre in data.get('genres', [])}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching genres: {e}")
        return {}
