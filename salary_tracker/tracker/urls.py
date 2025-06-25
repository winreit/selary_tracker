from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add-work/', views.add_work, name='add_work'),
    path('delete-last/', views.delete_last_work, name='delete_last'),
    path('save-month/', views.save_month, name='save_month'),
    path('month-stats/', views.month_stats, name='month_stats'),
    path('all-time-stats/', views.all_time_stats, name='all_time_stats'),
]