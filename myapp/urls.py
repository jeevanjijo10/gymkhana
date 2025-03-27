from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.home, name='home'),  # Maps the root URL to the `home` view
    path('recommend/', views.recommend, name='recommend'),  # Maps the `/recommend/` URL to the `recommend` view
    path("login/", views.login_view, name="login"),
    path("register/", views.register, name="register"),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('save-workout-plan/', views.save_workout_plan, name='save_workout_plan'), 
    path('saved-workout-plan/', views.saved_workout_plan, name='saved_workout_plan'),
    path('book/<int:class_id>/', views.book_class, name='book_class'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('trainers/', views.trainer_list, name='trainer_list'),
    path('logout/', views.logoutView, name='logout'),
]