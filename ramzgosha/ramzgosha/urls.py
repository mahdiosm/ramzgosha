# ramzgosha/urls.py
from django.contrib import admin
from django.urls import path
from puzzles import views
from django.contrib.auth import views as auth_views # این خط اضافه شود

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='puzzles/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('play/<str:date_str>/', views.play_puzzle, name='play'),
    path('api/reveal/<int:puzzle_id>/', views.reveal_letter, name='reveal_letter'),
    path('api/archive/load-more/', views.load_more_archive, name='load_more_archive'),
    path('archive/calendar/', views.archive_calendar, name='archive_calendar'),
    path('archive/calendar/<int:year>/<int:month>/', views.archive_calendar, name='archive_calendar_date'),
    path('create/', views.create_puzzle, name='create_puzzle'),
    path('my-puzzles/', views.my_puzzles, name='my_puzzles'),
    path('my-puzzles/<int:puzzle_id>/', views.play_private, name='play_private'),
    path('admin-review/', views.admin_review_puzzles, name='admin_review_puzzles'),
]