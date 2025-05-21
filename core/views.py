
import requests
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from .utils import *
from datetime import datetime


def home(request):
    movie_genres = get_genre_mapping("movie")
    series_genres = get_genre_mapping("tv")
    
    # URLs for different content types
    trending_movie_url = "https://api.themoviedb.org/3/trending/movie/week"
    trending_series_url = "https://api.themoviedb.org/3/trending/tv/week"
    anime_series_url = "https://api.themoviedb.org/3/discover/tv"
    
    params = {
        "api_key": settings.TMDB_API_KEY,
        "language": "en-US"
    }

    hero_content = []  # Combined hero content (unchanged)
    movies = []
    series = []
    anime_series = []  # New: Just for Japanese anime

    try:
        # 1. Fetch trending movies (unchanged from your original)
        movie_response = requests.get(trending_movie_url, params=params)
        movie_response.raise_for_status()
        movie_data = movie_response.json()

        for movie in movie_data.get("results", [])[:3]:
            hero_content.append({
                'title': movie.get('title'),
                'backdrop_path': f"https://image.tmdb.org/t/p/original{movie.get('backdrop_path')}" if movie.get('backdrop_path') else None,
                'poster_path': f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get('poster_path') else None,
                'vote_average': round(movie.get('vote_average', 0)),
                'release_date': movie.get('release_date', 'N/A'),
                'runtime': '2h 15m',
                'genres': [movie_genres.get(genre_id, 'Unknown') for genre_id in movie.get('genre_ids', [])][:3],
                'overview': movie.get('overview', 'No description available.'),
                'id': movie.get('id'),
                'content_type': 'movie'
            })
        
        movies = movie_data.get("results", [])

        # 2. Fetch trending series (unchanged from your original)
        series_response = requests.get(trending_series_url, params=params)
        series_response.raise_for_status()
        series_data = series_response.json()

        for show in series_data.get("results", [])[:13]:  # Keep your original 3 series
            hero_content.append({
                'title': show.get('name'),
                'backdrop_path': f"https://image.tmdb.org/t/p/original{show.get('backdrop_path')}" if show.get('backdrop_path') else None,
                'poster_path': f"https://image.tmdb.org/t/p/w500{show.get('poster_path')}" if show.get('poster_path') else None,
                'vote_average': round(show.get('vote_average', 0)),
                'release_date': show.get('first_air_date', 'N/A'),
                'runtime': 'N/A',
                'genres': [series_genres.get(genre_id, 'Unknown') for genre_id in show.get('genre_ids', [])][:3],
                'overview': show.get('overview', 'No description available.'),
                'id': show.get('id'),
                'content_type': 'tv'
            })

        series = series_data.get("results", [])

        # 3. NEW: Improved Japanese anime series fetching
        anime_params = {
            **params,
            "with_genres": "16",  # Animation genre ID
            "with_original_language": "ja",  # Japanese language
            "sort_by": "vote_average.desc",  # Sort by highest rating
            "vote_count.gte": 100,  # Only shows with significant votes
            "first_air_date.lte": datetime.now().strftime("%Y-%m-%d"),  # Only aired shows
            "first_air_date.gte": "2020-01-01",  # Only recent shows (last 4 years)
            "without_genres": "10762,10763,10764,10767",  # Exclude kids, news, talk, soap shows
            "include_null_first_air_dates": False,  # Exclude shows without air dates
            "page": 1
        }
        
        anime_response = requests.get(anime_series_url, params=anime_params)
        anime_response.raise_for_status()
        anime_data = anime_response.json()

        # Additional filtering to ensure quality
        def is_valid_anime(anime):
            has_poster = anime.get('poster_path') is not None
            has_backdrop = anime.get('backdrop_path') is not None
            has_release = anime.get('first_air_date') is not None
            not_future = (
                has_release and 
                datetime.strptime(anime['first_air_date'], "%Y-%m-%d") <= datetime.now()
            )
            return has_poster and has_backdrop and has_release and not_future

        # Process anime series with additional quality checks
        anime_series = [{
            **anime,
            'genre_names': [series_genres.get(gid, 'Animation') for gid in anime.get('genre_ids', [])][:3]
        } for anime in anime_data.get("results", []) if is_valid_anime(anime)][:12]  # Limit to 12 best matches

        # Shuffle hero content (unchanged)
        import random
        random.shuffle(hero_content)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching from TMDB API: {e}")

    context = {
        'hero_content': hero_content,  # Unchanged
        'movies': movies,  # Unchanged
        'series': series,  # Unchanged
        'anime_series': anime_series  # NEW: Only for the anime section
    }
    return render(request, "./movies/home.html", context)





def watch_movie(request, tmdb_id, content_type):
    import requests
    from django.conf import settings
    
    api_key = settings.TMDB_API_KEY
    
    if content_type == 'movie':
        # Existing movie logic
        movie_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
        movie_params = {"api_key": api_key, "language": "en-US"}
        response = requests.get(movie_url, params=movie_params)
        content = response.json()
        
        # Get related movies
        related = []
        if content.get("genres"):
            first_genre_id = content["genres"][0]["id"]
            discover_url = f"https://api.themoviedb.org/3/discover/movie"
            discover_params = {
                "api_key": api_key,
                "with_genres": first_genre_id,
                "language": "en-US",
                "sort_by": "popularity.desc",
            }
            related_response = requests.get(discover_url, params=discover_params)
            related = related_response.json().get("results", [])
            
        return render(request, "./movies/watch.html", {
            "tmdb_id": tmdb_id,
            "content": content,
            "related": related,
        })
    
    elif content_type == 'tv':
        # Get TV show details
        tv_url = f"https://api.themoviedb.org/3/tv/{tmdb_id}"
        tv_params = {"api_key": api_key, "language": "en-US"}
        response = requests.get(tv_url, params=tv_params)
        content = response.json()

        selected_season = request.GET.get('season')
        selected_episode = request.GET.get('episode')
        
        # Get all seasons
        seasons = []
        if content.get("seasons"):
            for season in content["seasons"]:
                season_url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{season['season_number']}"
                season_params = {"api_key": api_key, "language": "en-US"}
                season_response = requests.get(season_url, params=season_params)
                seasons.append(season_response.json())
        
        # Get related TV shows
        related = []
        if content.get("genres"):
            first_genre_id = content["genres"][0]["id"]
            discover_url = f"https://api.themoviedb.org/3/discover/tv"
            discover_params = {
                "api_key": api_key,
                "with_genres": first_genre_id,
                "language": "en-US",
                "sort_by": "popularity.desc",
            }
            related_response = requests.get(discover_url, params=discover_params)
            related = related_response.json().get("results", [])
            
        return render(request, "./movies/tv.html", {
            "tmdb_id": tmdb_id,
            "content": content,
            "seasons": seasons,
            "related": related,
            "selected_season": selected_season,
            "selected_episode": selected_episode,
        })



def search_movies(request):
    query = request.GET.get('query', '')
    
    if not query:
        return JsonResponse({'results': []})
    
    # Search both movies and TV shows
    search_url = "https://api.themoviedb.org/3/search/multi"
    params = {
        'api_key': settings.TMDB_API_KEY,
        'query': query,
        'language': 'en-US',
        'page': 1,
        'include_adult': False
    }
    
    try:
        response = requests.get(search_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Process results to get what we need
        results = []
        for item in data.get('results', [])[:10]:  # Limit to 10 results
            if item.get('media_type') in ['movie', 'tv']:  # Include both movies and TV shows
                # Determine the correct title and year based on media type
                title = item.get('title') or item.get('name')
                year = None
                
                if item.get('media_type') == 'movie' and item.get('release_date'):
                    year = item.get('release_date')[:4]
                elif item.get('media_type') == 'tv' and item.get('first_air_date'):
                    year = item.get('first_air_date')[:4]
                
                results.append({
                    'id': item.get('id'),
                    'title': title,
                    'poster_path': item.get('poster_path'),
                    'media_type': item.get('media_type'),
                    'year': year,
                    'overview': item.get('overview', '')[:100] + '...' if item.get('overview') else 'No description available'
                })
        
        return JsonResponse({'results': results})
        
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)



def similar_content(request, content_id, content_type):
    api_key = settings.TMDB_API_KEY
    
    if content_type == 'movie':
        # Get similar movies
        url = f"https://api.themoviedb.org/3/movie/{content_id}/similar"
    else:
        # Get similar TV shows
        url = f"https://api.themoviedb.org/3/tv/{content_id}/similar"
    
    params = {"api_key": api_key, "language": "en-US"}
    response = requests.get(url, params=params)
    similar_content = response.json().get('results', [])[:6]
    
    return JsonResponse({
        'similar': similar_content,
        'content_type': content_type
    })
