
from django.contrib import admin
from .models import WorkType, UserProfile, Work, MonthlyTotal

@admin.register(WorkType)
class WorkTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'register_date')

@admin.register(Work)
class WorkAdmin(admin.ModelAdmin):
    list_display = ('user', 'work_type', 'date', 'month', 'year')
    list_filter = ('user', 'work_type')

@admin.register(MonthlyTotal)
class MonthlyTotalAdmin(admin.ModelAdmin):
    list_display = ('user', 'month', 'year', 'total', 'save_date')
    list_filter = ('user', 'year', 'month')