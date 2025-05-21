from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('watch/movie/<int:tmdb_id>/', views.watch_movie, {'content_type': 'movie'}, name='watch_movie'),
    path('search/', views.search_movies, name='search_movies'),
    path('watch/tv/<int:tmdb_id>/', views.watch_movie, {'content_type': 'tv'}, name='watch_tv'),
    path('api/similar/<int:content_id>/<str:content_type>/', views.similar_content, name='similar_content'),
]