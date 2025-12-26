# clear_database.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myportfolio.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import (
    Specialization, Department, Doctor, Service,
    DoctorSchedule, Patient, Appointment, Review,
    News, Contact, Slider
)
from django.db import connection

def clear_all_data():
    print("Очистка всей базы данных...")
    
    # Вариант A: Удалить все объекты в правильном порядке (чтобы избежать ForeignKey ошибок)
    try:
        # Удаляем в обратном порядке создания (сначала дочерние таблицы)
        Review.objects.all().delete()
        Appointment.objects.all().delete()
        Patient.objects.all().delete()
        DoctorSchedule.objects.all().delete()
        Doctor.objects.all().delete()
        Service.objects.all().delete()
        Department.objects.all().delete()
        Specialization.objects.all().delete()
        News.objects.all().delete()
        Contact.objects.all().delete()
        Slider.objects.all().delete()
        
        # Удаляем всех пользователей кроме superuser
        User.objects.filter(is_superuser=False).delete()
        
        print("✅ Все данные удалены!")
        
    except Exception as e:
        print(f"❌ Ошибка при удалении: {e}")

def clear_and_reset_sequences():
    """Полностью очистить БД и сбросить автоинкрементные счетчики (только для SQLite)"""
    print("Полная очистка базы данных с сбросом счетчиков...")
    
    models = [
        Review, Appointment, Patient, DoctorSchedule,
        Doctor, Service, Department, Specialization,
        News, Contact, Slider
    ]
    
    # Удаляем все объекты
    for model in models:
        model.objects.all().delete()
        print(f"Очищено: {model.__name__}")
    
    # Удаляем обычных пользователей
    User.objects.filter(is_superuser=False).delete()
    print(f"Очищено: User (кроме superuser)")
    
    # Сброс счетчиков автоинкремента для SQLite
    cursor = connection.cursor()
    tables = [
        'main_review', 'main_appointment', 'main_patient', 
        'main_doctorschedule', 'main_doctor', 'main_service',
        'main_department', 'main_specialization', 'main_news',
        'main_contact', 'main_slider', 'auth_user'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}';")
        except:
            pass
    
    connection.commit()
    print("✅ Все данные удалены и счетчики сброшены!")

if __name__ == '__main__':
    clear_all_data()  # или clear_and_reset_sequences()