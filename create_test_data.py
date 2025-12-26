# create_test_data.py
import os
import django
import random
from datetime import datetime, timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myportfolio.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import (
    Specialization, Department, Doctor, Service,
    DoctorSchedule, Patient, Appointment, Review,
    News, Contact, Slider
)

def create_test_data():
    print("Создание тестовых данных...")
    
    # Сначала очистим старые данные (опционально)
    print("Очистка старых данных...")
    # Раскомментируйте при необходимости:
    # User.objects.filter(is_superuser=False).delete()
    # Doctor.objects.all().delete()
    # Patient.objects.all().delete()
    
    # ==================== 1. СОЗДАНИЕ ПОЛЬЗОВАТЕЛЕЙ ДЛЯ ВРАЧЕЙ ====================
    print("\n1. Создание пользователей для врачей...")
    doctor_users = []
    doctor_credentials = []  # Будем хранить логины/пароли для вывода
    
    doctor_user_data = [
        {'username': 'dr_petrov', 'email': 'dr.petrov@clinic.ru', 'first_name': 'Иван', 'last_name': 'Петров'},
        {'username': 'dr_sidorova', 'email': 'dr.sidorova@clinic.ru', 'first_name': 'Мария', 'last_name': 'Сидорова'},
        {'username': 'dr_smirnov', 'email': 'dr.smirnov@clinic.ru', 'first_name': 'Алексей', 'last_name': 'Смирнов'},
        {'username': 'dr_kuznetsova', 'email': 'dr.kuznetsova@clinic.ru', 'first_name': 'Елена', 'last_name': 'Кузнецова'},
        {'username': 'dr_vasiliev', 'email': 'dr.vasiliev@clinic.ru', 'first_name': 'Дмитрий', 'last_name': 'Васильев'},
    ]
    
    for i, user_data in enumerate(doctor_user_data):
        # Проверяем, существует ли уже пользователь
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'is_staff': True,  # Врачи имеют доступ к админке (опционально)
            }
        )
        
        # Устанавливаем пароль для всех врачей одинаковый (для тестирования)
        password = 'doctor123'  # Пароль для всех врачей
        user.set_password(password)
        user.save()
        
        doctor_users.append(user)
        doctor_credentials.append({
            'username': user.username,
            'password': password,
            'full_name': f"{user.last_name} {user.first_name}"
        })
        
        print(f"   Создан пользователь для врача: {user.username} (пароль: {password})")
    
    # ==================== 2. СОЗДАНИЕ ПОЛЬЗОВАТЕЛЕЙ ДЛЯ ПАЦИЕНТОВ ====================
    print("\n2. Создание пользователей для пациентов...")
    patient_users = []
    patient_credentials = []
    
    for i in range(1, 6):
        username = f'patient{i}'
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': f'Пациент{i}',
                'last_name': f'Тестовый{i}',
                'email': f'patient{i}@test.com',
            }
        )
        
        password = 'patient123'  # Пароль для всех пациентов
        user.set_password(password)
        user.save()
        
        patient_users.append(user)
        patient_credentials.append({
            'username': user.username,
            'password': password,
            'full_name': f"{user.last_name} {user.first_name}"
        })
        
        print(f"   Создан пользователь для пациента: {user.username} (пароль: {password})")
    
    # ==================== 3. СПЕЦИАЛИЗАЦИИ ====================
    print("\n3. Создание специализаций...")
    specializations = []
    spec_names = [
        'Терапевт', 'Хирург', 'Кардиолог', 'Невролог', 
        'Офтальмолог', 'Отоларинголог', 'Гинеколог', 'Уролог',
        'Эндокринолог', 'Дерматолог', 'Стоматолог', 'Педиатр'
    ]
    
    for name in spec_names:
        spec, created = Specialization.objects.get_or_create(
            name=name,
            defaults={'description': f'Описание {name.lower()}'}
        )
        specializations.append(spec)
        print(f"   Создана специализация: {name}")
    
    # ==================== 4. ОТДЕЛЕНИЯ ====================
    print("\n4. Создание отделений...")
    departments = []
    dept_data = [
        {'name': 'Терапевтическое отделение', 'floor': 1, 'phone': '+7(111)111-11-11'},
        {'name': 'Хирургическое отделение', 'floor': 2, 'phone': '+7(222)222-22-22'},
        {'name': 'Кардиологическое отделение', 'floor': 3, 'phone': '+7(333)333-33-33'},
        {'name': 'Неврологическое отделение', 'floor': 4, 'phone': '+7(444)444-44-44'},
        {'name': 'Педиатрическое отделение', 'floor': 1, 'phone': '+7(555)555-55-55'},
    ]
    
    for dept in dept_data:
        department, created = Department.objects.get_or_create(
            name=dept['name'],
            defaults=dept
        )
        departments.append(department)
        print(f"   Создано отделение: {dept['name']}")
    
    # ==================== 5. ВРАЧИ (С ПРИВЯЗКОЙ К ПОЛЬЗОВАТЕЛЯМ) ====================
    print("\n5. Создание врачей с привязкой к пользователям...")
    doctors = []
    doctor_names = [
        ('Иван', 'Петров', 'Иванович'),
        ('Мария', 'Сидорова', 'Александровна'),
        ('Алексей', 'Смирнов', 'Владимирович'),
        ('Елена', 'Кузнецова', 'Сергеевна'),
        ('Дмитрий', 'Васильев', 'Петрович'),
        ('Ольга', 'Попова', 'Игоревна'),
        ('Сергей', 'Новиков', 'Андреевич'),
        ('Анна', 'Федорова', 'Михайловна'),
        ('Андрей', 'Морозов', 'Викторович'),
        ('Татьяна', 'Волкова', 'Николаевна'),
    ]
    
    categories = ['none', 'second', 'first', 'highest']
    
    for i, (first_name, last_name, middle_name) in enumerate(doctor_names):
        # Для первых 5 врачей привязываем созданных пользователей
        # Для остальных создаем без пользователей (или можно создать новых)
        if i < len(doctor_users):
            user = doctor_users[i]
        else:
            # Для врачей без специальных пользователей создаем обычного пользователя
            username = f"dr_{last_name.lower()}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': f'{username}@clinic.ru',
                }
            )
            user.set_password('doctor123')
            user.save()
        
        # Создаем врача с привязкой к пользователю
        doctor = Doctor.objects.create(
            user=user,  # ВАЖНО: привязываем пользователя
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            specialization=random.choice(specializations),
            department=random.choice(departments),
            category=random.choice(categories),
            experience=random.randint(5, 30),
            education=f'Высшее медицинское образование, {random.randint(1990, 2015)} год',
            qualifications='Сертификаты по специальности, курсы повышения квалификации',
            phone=f'+7(900){random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}',
            email=user.email,  # Используем email пользователя
            bio=f'Врач высшей квалификации с опытом работы более {random.randint(5, 30)} лет. Специализируется на лечении заболеваний.',
            is_active=True,
            consultation_duration=random.choice([30, 45, 60]),
            consultation_price=random.choice([1500, 2000, 2500, 3000, 0]),
            order=i
        )
        doctors.append(doctor)
        print(f"   Создан врач: {doctor.full_name()} ({doctor.specialization.name})")
        print(f"     Пользователь: {user.username}, Пароль: doctor123")
    
    # ==================== 6. УСЛУГИ ====================
    print("\n6. Создание услуг...")
    services = []
    service_data = [
        {'name': 'Консультация терапевта', 'category': 'consultation', 'price': 1500, 'duration': 30},
        {'name': 'Консультация хирурга', 'category': 'consultation', 'price': 2000, 'duration': 45},
        {'name': 'Консультация кардиолога', 'category': 'consultation', 'price': 2500, 'duration': 45},
        {'name': 'Общий анализ крови', 'category': 'analysis', 'price': 800, 'duration': 15},
        {'name': 'УЗИ брюшной полости', 'category': 'diagnostics', 'price': 3000, 'duration': 60},
        {'name': 'ЭКГ', 'category': 'diagnostics', 'price': 1200, 'duration': 30},
        {'name': 'Массаж спины', 'category': 'treatment', 'price': 2000, 'duration': 45},
        {'name': 'Физиотерапия', 'category': 'treatment', 'price': 1500, 'duration': 40},
        {'name': 'Вакцинация от гриппа', 'category': 'procedure', 'price': 0, 'duration': 15, 'is_free': True},
        {'name': 'Диспансеризация', 'category': 'consultation', 'price': 0, 'duration': 90, 'is_free': True},
    ]
    
    for service_info in service_data:
        service, created = Service.objects.get_or_create(
            name=service_info['name'],
            defaults={
                'category': service_info['category'],
                'description': f'Подробное описание услуги "{service_info["name"]}". Качественное оказание медицинской помощи.',
                'short_description': f'Услуга "{service_info["name"]}"',
                'price': service_info['price'],
                'duration': service_info['duration'],
                'is_free': service_info.get('is_free', False),
                'is_active': True,
            }
        )
        
        # Добавляем случайных врачей к услуге
        num_doctors = random.randint(2, 5)
        for doctor in random.sample(doctors, min(num_doctors, len(doctors))):
            service.doctors.add(doctor)
        
        services.append(service)
        print(f"   Создана услуга: {service.name}")
    
    # ==================== 7. ПАЦИЕНТЫ (С ПРИВЯЗКОЙ К ПОЛЬЗОВАТЕЛЯМ) ====================
    print("\n7. Создание пациентов...")
    patients = []
    
    for i, user in enumerate(patient_users):
        patient, created = Patient.objects.get_or_create(
            user=user,
            defaults={
                'birth_date': datetime(1980 + i, (i % 12) + 1, (i % 28) + 1).date(),
                'gender': random.choice(['M', 'F']),
                'insurance_policy': f'12345678901234{i:02d}',
                'phone': f'+7(900){random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}',
                'address': f'г. Москва, ул. Тестовая, д. {i+1}',
                'blood_type': random.choice(['0(I)+', 'A(II)+', 'B(III)+', 'AB(IV)+', '']),
                'allergies': 'Пыльца, пенициллин' if random.choice([True, False]) else '',
                'chronic_diseases': 'Гипертония, астма' if random.choice([True, False]) else '',
            }
        )
        patients.append(patient)
        print(f"   Создан пациент: {patient.user.get_full_name()}")
    
    # ==================== 8. РАСПИСАНИЕ ВРАЧЕЙ ====================
    print("\n8. Создание расписания врачей...")
    today = timezone.now().date()
    
    for doctor in doctors:
        for day_offset in range(14):  # На 2 недели вперед
            date = today + timedelta(days=day_offset)
            
            # Только рабочие дни (пн-пт)
            if date.weekday() < 5:  # 0-4 = пн-пт
                schedule, created = DoctorSchedule.objects.get_or_create(
                    doctor=doctor,
                    date=date,
                    defaults={
                        'start_time': '09:00',
                        'end_time': '18:00',
                        'break_start': '13:00',
                        'break_end': '14:00',
                        'slot_duration': doctor.consultation_duration,
                        'is_available': True,
                        'is_working_day': True,
                        'room': f'Кабинет {random.randint(100, 500)}',
                    }
                )
        print(f"   Создано расписание для врача: {doctor.full_name()}")
    
    # ==================== 9. ЗАПИСИ НА ПРИЕМ ====================
    print("\n9. Создание записей на прием...")
    statuses = ['pending', 'confirmed', 'completed', 'cancelled']
    
    for patient in patients:
        for _ in range(random.randint(1, 5)):  # 1-5 записей на пациента
            doctor = random.choice(doctors)
            service = random.choice(services)
            
            # Выбираем случайную дату в ближайшие 2 недели
            days_from_now = random.randint(1, 14)
            appointment_date = today + timedelta(days=days_from_now)
            
            # Получаем расписание врача на эту дату
            schedule = DoctorSchedule.objects.filter(
                doctor=doctor,
                date=appointment_date
            ).first()
            
            if schedule:
                # Создаем время приема
                appointment_time = timezone.make_aware(
                    datetime.combine(
                        appointment_date,
                        datetime.strptime('09:00', '%H:%M').time()
                    ) + timedelta(hours=random.randint(0, 8))
                )
                
                appointment = Appointment.objects.create(
                    patient=patient,
                    doctor=doctor,
                    service=service,
                    schedule=schedule,
                    appointment_time=appointment_time,
                    status=random.choice(statuses),
                    symptoms='Головная боль, слабость, повышенная температура' if random.choice([True, False]) else '',
                    notes='Пациент записался заранее' if random.choice([True, False]) else '',
                    created_by=patient.user,
                )
    
    print(f"   Создано записей: {Appointment.objects.count()}")
    
    # ==================== 10. ОТЗЫВЫ ====================
    print("\n10. Создание отзывов...")
    for patient in patients:
        for _ in range(random.randint(0, 3)):  # 0-3 отзыва
            doctor = random.choice(doctors)
            review = Review.objects.create(
                patient=patient,
                doctor=doctor,
                rating=random.randint(3, 5),
                comment=f'Очень хороший врач, внимательный и профессиональный. Рекомендую!',
                is_published=True,
            )
    
    print(f"   Создано отзывов: {Review.objects.count()}")
    
    # ==================== 11. НОВОСТИ ====================
    print("\n11. Создание новостей...")
    for i in range(1, 6):
        news = News.objects.create(
            title=f'Новость {i}: Важная информация для пациентов',
            slug=f'news-{i}',
            content=f'<p>Это текст новости номер {i}. Здесь важная информация о работе поликлиники, новых услугах, изменениях в расписании.</p><p>Будьте здоровы!</p>',
            excerpt=f'Краткое описание новости {i}',
            author=User.objects.filter(is_staff=True).first() or patient_users[0],
            is_published=True,
            published_at=timezone.now() - timedelta(days=i*7),
        )
        print(f"   Создана новость: {news.title}")
    
    # ==================== 12. КОНТАКТЫ ====================
    print("\n12. Создание контактов...")
    contacts_data = [
        {'type': 'phone', 'value': '+7 (495) 123-45-67', 'description': 'Единый телефон регистратуры', 'order': 1},
        {'type': 'phone', 'value': '+7 (495) 123-45-68', 'description': 'Справочная служба', 'order': 2},
        {'type': 'email', 'value': 'info@polyclinic.ru', 'description': 'Общая почта', 'order': 3},
        {'type': 'address', 'value': 'г. Москва, ул. Медицинская, д. 15', 'description': 'Основной адрес', 'order': 4},
        {'type': 'working_hours', 'value': 'Пн-Пт: 8:00-20:00, Сб: 9:00-18:00, Вс: 9:00-16:00', 'description': 'Режим работы', 'order': 5},
    ]
    
    for contact_info in contacts_data:
        Contact.objects.get_or_create(
            type=contact_info['type'],
            value=contact_info['value'],
            defaults=contact_info
        )
        print(f"   Создан контакт: {contact_info['description']}")
    
    # ==================== 13. СЛАЙДЕР ====================
    print("\n13. Создание слайдов...")
    for i in range(1, 4):
        Slider.objects.get_or_create(
            title=f'Слайд {i}',
            defaults={
                'description': f'Описание слайда {i}. Важная информация для пациентов.',
                'link': '/about/',
                'link_text': 'Подробнее',
                'order': i,
                'is_active': True,
            }
        )
        print(f"   Создан слайд: Слайд {i}")
    
    # ==================== ВЫВОД ИНФОРМАЦИИ ДЛЯ ТЕСТИРОВАНИЯ ====================
    print("\n" + "="*80)
    print("✅ ТЕСТОВЫЕ ДАННЫЕ СОЗДАНЫ УСПЕШНО!")
    print("="*80)
    
    print(f"\n📊 СТАТИСТИКА:")
    print(f"   👨‍⚕️  Врачей: {Doctor.objects.count()}")
    print(f"   👥  Пациентов: {Patient.objects.count()}")
    print(f"   🩺  Услуг: {Service.objects.count()}")
    print(f"   📅  Записей на прием: {Appointment.objects.count()}")
    print(f"   ⭐  Отзывов: {Review.objects.count()}")
    
    print(f"\n🔐 ДАННЫЕ ДЛЯ ВХОДА ВРАЧЕЙ:")
    print("   (Используйте обычную форму входа /login/)")
    print("-" * 40)
    for i, cred in enumerate(doctor_credentials[:5], 1):
        print(f"   {i}. Доктор {cred['full_name']}")
        print(f"      Логин: {cred['username']}")
        print(f"      Пароль: {cred['password']}")
    
    print(f"\n👤 ДАННЫЕ ДЛЯ ВХОДА ПАЦИЕНТОВ:")
    print("-" * 40)
    for i, cred in enumerate(patient_credentials[:3], 1):
        print(f"   {i}. Пациент {cred['full_name']}")
        print(f"      Логин: {cred['username']}")
        print(f"      Пароль: {cred['password']}")
    
    print(f"\n🚪 АДРЕСА ДЛЯ ТЕСТИРОВАНИЯ:")
    print(f"   • Главная страница: http://127.0.0.1:8000/")
    print(f"   • Вход в систему: http://127.0.0.1:8000/login/")
    print(f"   • Вход для врачей: http://127.0.0.1:8000/doctor/login/")
    print(f"   • Личный кабинет врача: http://127.0.0.1:8000/doctor/dashboard/")
    print(f"   • Личный кабинет пациента: http://127.0.0.1:8000/profile/")
    print(f"   • Список врачей: http://127.0.0.1:8000/doctors/")
    
    print("\n💡 ПОДСКАЗКА:")
    print("   1. Войдите как врач (dr_petrov / doctor123)")
    print("   2. Должны быть перенаправлены в кабинет врача")
    print("   3. В меню должна отображаться иконка врача 👨‍⚕️")

if __name__ == '__main__':
    create_test_data()