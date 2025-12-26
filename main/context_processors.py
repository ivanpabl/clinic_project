# main/context_processors.py
from .models import Doctor
from datetime import timedelta
from django.utils import timezone

def custom_filters(request):
    """Добавляем кастомные фильтры в контекст"""
    def add_days(date, days):
        return date + timedelta(days=days)
    
    def get_item(dictionary, key):
        return dictionary.get(key)
    
    week_days = [
        (0, 'Пн'), (1, 'Вт'), (2, 'Ср'), (3, 'Чт'), 
        (4, 'Пт'), (5, 'Сб'), (6, 'Вс')
    ]
    
    return {
        'add_days': add_days,
        'get_item': get_item,
        'week_days': week_days,
    }

def user_type(request):
    """Добавляет информацию о типе пользователя в контекст"""
    if request.user.is_authenticated:
        try:
            is_doctor = Doctor.objects.filter(user=request.user).exists()
        except:
            is_doctor = False
    else:
        is_doctor = False
    
    return {
        'is_doctor': is_doctor,
    }