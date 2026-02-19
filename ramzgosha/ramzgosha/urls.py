# ramzgosha/urls.py
from django.contrib import admin
from django.urls import path
from puzzles import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('play/<str:date_str>/', views.play_puzzle, name='play'),
    path('api/reveal/<str:date_str>/', views.reveal_letter, name='reveal_letter'),
    path('api/archive/load-more/', views.load_more_archive, name='load_more_archive'),
    path('archive/calendar/', views.archive_calendar, name='archive_calendar'),
    path('archive/calendar/<int:year>/<int:month>/', views.archive_calendar, name='archive_calendar_date'),
    path('create/', views.create_puzzle, name='create_puzzle'),
]