from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.utils import timezone
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponseRedirect
from datetime import datetime, timedelta, date

import json
from django.db import models

from .models import (
    Doctor, Service, Specialization, Department,
    Appointment, Patient, DoctorSchedule, Review,
    News, Contact, Slider
)
from .forms import (
    PatientRegistrationForm, AppointmentForm, 
    ReviewForm, PatientProfileForm, DoctorLoginForm
)

# ==================== ГЛАВНАЯ СТРАНИЦА И ОСНОВНЫЕ РАЗДЕЛЫ ====================

def home(request):
    """Главная страница"""
    # Получаем активные слайды
    sliders = Slider.objects.filter(is_active=True).order_by('order')
    
    # Получаем последние новости
    latest_news = News.objects.filter(
        is_published=True,
        published_at__lte=timezone.now()
    ).order_by('-published_at')[:3]
    
    # Получаем популярных врачей (с лучшим рейтингом)
    popular_doctors = Doctor.objects.filter(
        is_active=True
    ).order_by('-reviews__rating')[:6]
    
    # Получаем основные услуги
    main_services = Service.objects.filter(
        is_active=True,
        is_free=False
    ).order_by('order')[:6]
    
    context = {
        'title': 'Главная',
        'sliders': sliders,
        'latest_news': latest_news,
        'popular_doctors': popular_doctors,
        'main_services': main_services,
    }
    
    return render(request, 'main/home.html', context)


def about_clinic(request):
    """Страница 'О клинике'"""
    # Получаем отделения
    departments = Department.objects.all().order_by('name')
    
    # Получаем статистику
    doctors_count = Doctor.objects.filter(is_active=True).count()
    services_count = Service.objects.filter(is_active=True).count()
    
    context = {
        'title': 'О клинике',
        'departments': departments,
        'doctors_count': doctors_count,
        'services_count': services_count,
    }
    
    return render(request, 'main/about.html', context)


def contacts(request):
    """Страница контактов"""
    # Получаем все контакты
    contacts_list = Contact.objects.filter(is_active=True).order_by('order')
    
    # Группируем контакты по типам
    phones = contacts_list.filter(type='phone')
    emails = contacts_list.filter(type='email')
    addresses = contacts_list.filter(type='address')
    working_hours = contacts_list.filter(type='working_hours')
    
    context = {
        'title': 'Контакты',
        'phones': phones,
        'emails': emails,
        'addresses': addresses,
        'working_hours': working_hours,
    }
    
    return render(request, 'main/contacts.html', context)


# ==================== ВРАЧИ ====================

class DoctorListView(ListView):
    """Список всех врачей"""
    model = Doctor
    template_name = 'main/doctors/list.html'
    context_object_name = 'doctors'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Doctor.objects.filter(is_active=True)
        
        # Фильтрация по специализации
        specialization_id = self.request.GET.get('specialization')
        if specialization_id:
            queryset = queryset.filter(specialization_id=specialization_id)
        
        # Фильтрация по отделению
        department_id = self.request.GET.get('department')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        # Поиск по имени
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(last_name__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(middle_name__icontains=search_query) |
                Q(specialization__name__icontains=search_query)
            )
        
        return queryset.order_by('order', 'last_name', 'first_name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Врачи'
        context['specializations'] = Specialization.objects.all()
        context['departments'] = Department.objects.all()
        
        # Сохраняем параметры фильтрации для пагинации
        params = self.request.GET.copy()
        if 'page' in params:
            del params['page']
        context['filter_params'] = params.urlencode()
        
        return context


class DoctorDetailView(DetailView):
    """Детальная страница врача"""
    model = Doctor
    template_name = 'main/doctors/detail.html'
    context_object_name = 'doctor'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doctor = self.object
        
        # Получаем отзывы о враче
        reviews = Review.objects.filter(
            doctor=doctor,
            is_published=True
        ).order_by('-created_at')[:10]
        
        # Получаем услуги врача
        services = doctor.services.filter(is_active=True)
        
        # Получаем расписание на ближайшие 7 дней
        today = timezone.now().date()
        next_week = today + timedelta(days=7)
        
        schedule = DoctorSchedule.objects.filter(
            doctor=doctor,
            date__range=[today, next_week],
            is_available=True,
            is_working_day=True
        ).order_by('date')
        
        context.update({
            'title': f'Доктор {doctor.full_name()}',
            'reviews': reviews,
            'services': services,
            'schedule': schedule,
            'today': today,
            'next_week': next_week,
        })
        
        return context


def doctor_login(request):
    """Вход для врачей"""
    # Если пользователь уже авторизован
    if request.user.is_authenticated:
        # Проверяем, врач ли это
        try:
            if Doctor.objects.filter(user=request.user).exists():
                return redirect('doctor_dashboard')
            else:
                # Если это пациент, отправляем в его кабинет
                return redirect('profile')
        except:
            pass
    
    if request.method == 'POST':
        form = DoctorLoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Пытаемся аутентифицировать
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Проверяем, является ли пользователь врачом
                try:
                    doctor = Doctor.objects.get(user=user)
                    if doctor.is_active:
                        login(request, user)
                        
                        # Сохраняем в сессии, что это врач
                        request.session['is_doctor'] = True
                        request.session['doctor_id'] = doctor.id
                        
                        messages.success(request, f'Добро пожаловать, доктор {doctor.full_name()}!')
                        return redirect('doctor_dashboard')
                    else:
                        messages.error(request, 'Ваш аккаунт врача неактивен.')
                except Doctor.DoesNotExist:
                    messages.error(request, 'Этот аккаунт не принадлежит врачу.')
            else:
                messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = DoctorLoginForm()
    
    context = {
        'title': 'Вход для врачей',
        'form': form,
    }
    
    return render(request, 'main/auth/doctor_login.html', context)

@login_required
def doctor_dashboard(request):
    """Личный кабинет врача"""
    # Проверяем, является ли пользователь врачом
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Доступ только для врачей')
        return redirect('home')
    
    # Получаем сегодняшнюю дату
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    today = timezone.now().date()
    
    # Ближайшие записи
    upcoming_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_time__gte=timezone.now(),
        status__in=['pending', 'confirmed']
    ).order_by('appointment_time')[:5]
    
    # Сегодняшние записи
    todays_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_time__date=today,
        status__in=['pending', 'confirmed']
    ).order_by('appointment_time')
    
    context = {
        'title': 'Личный кабинет врача',
        'doctor': doctor,
        'upcoming_appointments': upcoming_appointments,
        'todays_appointments': todays_appointments,
        'today': today,
    }
    
    return render(request, 'main/doctor/dashboard.html', context)


@login_required
def doctor_schedule(request):
    """Просмотр расписания врача"""
    # Проверяем, является ли пользователь врачом
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Доступ только для врачей')
        return redirect('home')
    
    # Получаем параметры фильтрации
    date_filter = request.GET.get('date')
    status_filter = request.GET.get('status', 'all')
    
    # Базовый запрос
    appointments = Appointment.objects.filter(doctor=doctor)
    
    # Фильтрация по дате
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            appointments = appointments.filter(appointment_time__date=filter_date)
        except ValueError:
            messages.error(request, 'Некорректный формат даты')
    
    # Фильтрация по статусу
    if status_filter != 'all':
        appointments = appointments.filter(status=status_filter)
    
    # Сортируем по времени
    appointments = appointments.order_by('appointment_time')
    
    # Получаем уникальные даты для фильтра
    appointment_dates = Appointment.objects.filter(
        doctor=doctor
    ).dates('appointment_time', 'day').order_by('-appointment_time')
    
    # Группируем записи по дате для удобного отображения
    appointments_by_date = {}
    for appointment in appointments:
        date_key = appointment.appointment_time.date()
        if date_key not in appointments_by_date:
            appointments_by_date[date_key] = []
        appointments_by_date[date_key].append(appointment)
    
    # Сортируем даты
    sorted_dates = sorted(appointments_by_date.keys(), reverse=True)
    
    # Вычисляем завтрашнюю дату
    from datetime import timedelta
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    
    context = {
        'title': 'Мое расписание',
        'doctor': doctor,
        'appointments': appointments,
        'appointments_by_date': appointments_by_date,
        'sorted_dates': sorted_dates,
        'appointment_dates': appointment_dates[:10],  # последние 10 дат
        'status_filter': status_filter,
        'date_filter': date_filter,
        'status_choices': Appointment.STATUS_CHOICES,
        'today': today,
        'tomorrow': tomorrow,
    }
    
    return render(request, 'main/doctor/schedule.html', context)


@login_required
def doctor_appointment_detail(request, pk):
    """Детальная информация о записи для врача"""
    # Проверяем, является ли пользователь врачом
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Доступ только для врачей')
        return redirect('home')
    
    # Получаем запись
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Проверяем, что запись принадлежит этому врачу
    if appointment.doctor != doctor:
        messages.error(request, 'Эта запись не принадлежит вам')
        return redirect('doctor_schedule')
    
    if request.method == 'POST':
        # Обработка изменения статуса
        new_status = request.POST.get('status')
        notes = request.POST.get('doctor_notes', '')
        
        if new_status in dict(Appointment.STATUS_CHOICES):
            old_status = appointment.status
            appointment.status = new_status
            
            # Добавляем заметки врача
            if notes:
                if appointment.notes:
                    appointment.notes += f"\n\n--- Заметки врача ({timezone.now().strftime('%d.%m.%Y %H:%M')}) ---\n{notes}"
                else:
                    appointment.notes = f"--- Заметки врача ({timezone.now().strftime('%d.%m.%Y %H:%M')}) ---\n{notes}"
            
            appointment.save()
            
            messages.success(request, f'Статус записи изменен с "{dict(Appointment.STATUS_CHOICES)[old_status]}" на "{dict(Appointment.STATUS_CHOICES)[new_status]}"')
            return redirect('doctor_appointment_detail', pk=appointment.pk)
    
    patient_appointments = Appointment.objects.filter(
        patient=appointment.patient
    ).exclude(
        id=appointment.id
    ).order_by('-appointment_time')[:5]
    
    context = {
        'title': f'Запись #{appointment.appointment_number}',
        'appointment': appointment,
        'status_choices': Appointment.STATUS_CHOICES,
        'patient_appointments': patient_appointments,  # добавляем в контекст
    }
    
    return render(request, 'main/doctor/appointment_detail.html', context)


@login_required
def doctor_working_schedule(request):
    """Управление рабочим расписанием врача"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Доступ только для врачей')
        return redirect('home')
    
    # Получаем параметры
    month = request.GET.get('month')
    year = request.GET.get('year')
    
    # Определяем текущий месяц и год
    today = timezone.now().date()
    current_year = today.year
    current_month = today.month
    
    if year and month:
        try:
            current_year = int(year)
            current_month = int(month)
        except ValueError:
            current_year = today.year
            current_month = today.month
    
    # Получаем расписание на месяц
    start_date = date(current_year, current_month, 1)
    
    # Определяем последний день месяца
    if current_month == 12:
        end_date = date(current_year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(current_year, current_month + 1, 1) - timedelta(days=1)
    
    schedules = DoctorSchedule.objects.filter(
        doctor=doctor,
        date__range=[start_date, end_date]
    ).order_by('date')
    
    # Создаем календарь на месяц
    import calendar
    cal = calendar.Calendar()
    month_days = cal.monthdatescalendar(current_year, current_month)
    
    # Подготовка данных для календаря
    schedule_dict = {schedule.date: schedule for schedule in schedules}
    
    # Навигация по месяцам
    prev_month = current_month - 1 if current_month > 1 else 12
    prev_year = current_year if current_month > 1 else current_year - 1
    next_month = current_month + 1 if current_month < 12 else 1
    next_year = current_year if current_month < 12 else current_year + 1
    
    if request.method == 'POST':
        # Обработка создания/изменения расписания
        date_str = request.POST.get('date')
        action = request.POST.get('action')
        
        if date_str and action:
            try:
                schedule_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                if action == 'add':
                    # Создаем расписание на день
                    schedule, created = DoctorSchedule.objects.get_or_create(
                        doctor=doctor,
                        date=schedule_date,
                        defaults={
                            'start_time': '09:00',
                            'end_time': '18:00',
                            'slot_duration': doctor.consultation_duration,
                            'is_available': True,
                            'is_working_day': True,
                            'room': 'Основной кабинет',
                        }
                    )
                    if created:
                        messages.success(request, f'Расписание на {schedule_date.strftime("%d.%m.%Y")} создано')
                    else:
                        messages.info(request, f'Расписание на {schedule_date.strftime("%d.%m.%Y")} уже существует')
                
                elif action == 'remove':
                    # Удаляем расписание
                    deleted, _ = DoctorSchedule.objects.filter(
                        doctor=doctor,
                        date=schedule_date
                    ).delete()
                    if deleted:
                        messages.success(request, f'Расписание на {schedule_date.strftime("%d.%m.%Y")} удалено')
                
                elif action == 'toggle':
                    # Изменяем доступность
                    schedule = DoctorSchedule.objects.filter(
                        doctor=doctor,
                        date=schedule_date
                    ).first()
                    if schedule:
                        schedule.is_available = not schedule.is_available
                        schedule.save()
                        status = "доступен" if schedule.is_available else "недоступен"
                        messages.success(request, f'Прием на {schedule_date.strftime("%d.%m.%Y")} теперь {status}')
                
                return redirect('doctor_working_schedule')
                
            except ValueError:
                messages.error(request, 'Некорректная дата')
    
    context = {
        'title': 'Мое рабочее расписание',
        'doctor': doctor,
        'schedules': schedules,
        'schedule_dict': schedule_dict,
        'month_days': month_days,
        'current_year': current_year,
        'current_month': current_month,
        'month_name': ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'][current_month - 1],
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'today': today,
    }
    
    return render(request, 'main/doctor/working_schedule.html', context)


@login_required
def doctor_schedule_day(request, date_str):
    """Расписание врача на конкретный день"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Доступ только для врачей')
        return redirect('home')
    
    try:
        schedule_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Некорректная дата')
        return redirect('doctor_schedule')
    
    # Получаем расписание на этот день
    schedule = DoctorSchedule.objects.filter(
        doctor=doctor,
        date=schedule_date
    ).first()
    
    # Получаем записи на этот день
    appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_time__date=schedule_date
    ).order_by('appointment_time')
    
    # Если нет расписания, создаем временное
    if not schedule:
        schedule = DoctorSchedule(
            doctor=doctor,
            date=schedule_date,
            start_time='09:00',
            end_time='18:00',
            slot_duration=doctor.consultation_duration,
            is_available=False,
            is_working_day=False,
        )
    
    # Получаем доступные слоты
    available_slots = []
    if schedule and schedule.is_available and schedule.is_working_day:
        available_slots = schedule.get_available_slots()
    
    context = {
        'title': f'Расписание на {schedule_date.strftime("%d.%m.%Y")}',
        'doctor': doctor,
        'schedule_date': schedule_date,
        'schedule': schedule,
        'appointments': appointments,
        'available_slots': available_slots,
    }
    
    return render(request, 'main/doctor/schedule_day.html', context)


@login_required
def doctor_statistics(request):
    """Статистика врача"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'Доступ только для врачей')
        return redirect('home')
    
    # Период для статистики (последние 30 дней)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Статистика по записям
    appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_time__date__range=[start_date, end_date]
    )
    
    # По статусам
    by_status = appointments.values('status').annotate(count=models.Count('id'))
    status_stats = {item['status']: item['count'] for item in by_status}
    
    # По дням недели
    appointments_by_weekday = appointments.extra({
        'weekday': "strftime('%w', appointment_time)"
    }).values('weekday').annotate(count=models.Count('id'))
    
    # По времени суток
    morning_appointments = appointments.filter(
        appointment_time__hour__gte=9,
        appointment_time__hour__lt=12
    ).count()
    
    day_appointments = appointments.filter(
        appointment_time__hour__gte=12,
        appointment_time__hour__lt=17
    ).count()
    
    evening_appointments = appointments.filter(
        appointment_time__hour__gte=17,
        appointment_time__hour__lt=20
    ).count()
    
    # Самые популярные услуги
    popular_services = appointments.values(
        'service__name'
    ).annotate(
        count=models.Count('id')
    ).order_by('-count')[:5]
    
    # Отзывы
    reviews = Review.objects.filter(doctor=doctor, is_published=True)
    avg_rating = reviews.aggregate(models.Avg('rating'))['rating__avg'] or 0
    
    context = {
        'title': 'Моя статистика',
        'doctor': doctor,
        'start_date': start_date,
        'end_date': end_date,
        'total_appointments': appointments.count(),
        'status_stats': status_stats,
        'appointments_by_weekday': appointments_by_weekday,
        'morning_appointments': morning_appointments,
        'day_appointments': day_appointments,
        'evening_appointments': evening_appointments,
        'popular_services': popular_services,
        'avg_rating': avg_rating,
        'reviews_count': reviews.count(),
    }
    
    return render(request, 'main/doctor/statistics.html', context)


# ==================== УСЛУГИ ====================

class ServiceListView(ListView):
    """Список всех услуг"""
    model = Service
    template_name = 'main/services/list.html'
    context_object_name = 'services'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Service.objects.filter(is_active=True)
        
        # Фильтрация по категории
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Фильтрация по цене (бесплатные/платные)
        price_filter = self.request.GET.get('price')
        if price_filter == 'free':
            queryset = queryset.filter(is_free=True)
        elif price_filter == 'paid':
            queryset = queryset.filter(is_free=False)
        
        # Поиск по названию
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        return queryset.order_by('order', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Услуги'
        context['categories'] = Service.SERVICE_CATEGORIES
        
        # Сохраняем параметры фильтрации
        params = self.request.GET.copy()
        if 'page' in params:
            del params['page']
        context['filter_params'] = params.urlencode()
        
        return context


class ServiceDetailView(DetailView):
    """Детальная страница услуги"""
    model = Service
    template_name = 'main/services/detail.html'
    context_object_name = 'service'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = self.object
        
        # Получаем врачей, оказывающих эту услугу
        doctors = service.doctors.filter(is_active=True)
        
        context.update({
            'title': service.name,
            'doctors': doctors,
        })
        
        return context


# ==================== ЗАПИСЬ НА ПРИЕМ ====================

@login_required
def appointment_step1(request):
    """Шаг 1: Выбор специализации/услуги"""
    specializations = Specialization.objects.all()
    services = Service.objects.filter(is_active=True)
    
    if request.method == 'POST':
        service_id = request.POST.get('service')
        specialization_id = request.POST.get('specialization')
        
        if service_id:
            request.session['appointment_service_id'] = service_id
            return redirect('appointment_step2')
        elif specialization_id:
            request.session['appointment_specialization_id'] = specialization_id
            return redirect('appointment_step2_doctors')
    
    context = {
        'title': 'Запись на прием - Шаг 1',
        'specializations': specializations,
        'services': services,
    }
    
    return render(request, 'main/appointment/step1.html', context)


@login_required
def appointment_step2(request, service_id=None):
    """Шаг 2: Выбор врача (через услугу)"""
    if service_id:
        service = get_object_or_404(Service, id=service_id)
        doctors = service.doctors.filter(is_active=True)
    else:
        service_id = request.session.get('appointment_service_id')
        if not service_id:
            return redirect('appointment_step1')
        
        service = get_object_or_404(Service, id=service_id)
        doctors = service.doctors.filter(is_active=True)
    
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        if doctor_id:
            request.session['appointment_doctor_id'] = doctor_id
            request.session['appointment_service_id'] = service_id
            return redirect('appointment_step3')
    
    context = {
        'title': 'Запись на прием - Шаг 2',
        'service': service,
        'doctors': doctors,
    }
    
    return render(request, 'main/appointment/step2.html', context)


@login_required
def appointment_step2_doctors(request):
    """Шаг 2: Выбор врача (через специализацию)"""
    specialization_id = request.session.get('appointment_specialization_id')
    if not specialization_id:
        return redirect('appointment_step1')
    
    specialization = get_object_or_404(Specialization, id=specialization_id)
    doctors = Doctor.objects.filter(
        specialization=specialization,
        is_active=True
    )
    
    if request.method == 'POST':
        doctor_id = request.POST.get('doctor')
        if doctor_id:
            request.session['appointment_doctor_id'] = doctor_id
            return redirect('appointment_step3')
    
    context = {
        'title': 'Запись на прием - Шаг 2',
        'specialization': specialization,
        'doctors': doctors,
    }
    
    return render(request, 'main/appointment/step2_doctors.html', context)


@login_required
def appointment_step3(request):
    """Шаг 3: Выбор даты"""
    doctor_id = request.session.get('appointment_doctor_id')
    if not doctor_id:
        return redirect('appointment_step1')
    
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    # Получаем доступные даты на ближайшие 14 дней
    today = timezone.now().date()
    end_date = today + timedelta(days=14)
    
    available_dates = []
    for i in range(14):
        check_date = today + timedelta(days=i)
        
        # Проверяем, есть ли расписание на эту дату
        schedule = DoctorSchedule.objects.filter(
            doctor=doctor,
            date=check_date,
            is_available=True,
            is_working_day=True
        ).first()
        
        if schedule and schedule.get_available_slots():
            available_dates.append(check_date)
    
    if request.method == 'POST':
        appointment_date = request.POST.get('appointment_date')
        if appointment_date:
            request.session['appointment_date'] = appointment_date
            return redirect('appointment_step4')
    
    context = {
        'title': 'Запись на прием - Шаг 3',
        'doctor': doctor,
        'available_dates': available_dates,
    }
    
    return render(request, 'main/appointment/step3.html', context)


@login_required
def appointment_step4(request):
    """Шаг 4: Выбор времени"""
    doctor_id = request.session.get('appointment_doctor_id')
    appointment_date_str = request.session.get('appointment_date')
    
    if not doctor_id or not appointment_date_str:
        return redirect('appointment_step1')
    
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    try:
        appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Некорректная дата')
        return redirect('appointment_step3')
    
    # Получаем расписание врача на выбранную дату
    schedule = DoctorSchedule.objects.filter(
        doctor=doctor,
        date=appointment_date,
        is_available=True,
        is_working_day=True
    ).first()
    
    if not schedule:
        messages.error(request, 'На выбранную дату нет свободных слотов')
        return redirect('appointment_step3')
    
    # Получаем доступные временные слоты
    available_slots = schedule.get_available_slots()
    
    if not available_slots:
        messages.error(request, 'На выбранную дату нет свободных слотов')
        return redirect('appointment_step3')
    
    if request.method == 'POST':
        appointment_time = request.POST.get('appointment_time')
        if appointment_time:
            request.session['appointment_time'] = appointment_time
            return redirect('appointment_step5')
    
    context = {
        'title': 'Запись на прием - Шаг 4',
        'doctor': doctor,
        'appointment_date': appointment_date,
        'schedule': schedule,
        'available_slots': available_slots,
    }
    
    return render(request, 'main/appointment/step4.html', context)


@login_required
def appointment_step5(request):
    """Шаг 5: Подтверждение и создание записи"""
    print("=" * 80)
    print("DEBUG: Начало appointment_step5")

    # Получаем все данные из сессии
    doctor_id = request.session.get('appointment_doctor_id')
    service_id = request.session.get('appointment_service_id')
    appointment_date_str = request.session.get('appointment_date')
    appointment_time_str = request.session.get('appointment_time')

    print(f"DEBUG: doctor_id = {doctor_id}")
    print(f"DEBUG: service_id = {service_id}")
    print(f"DEBUG: appointment_date_str = {appointment_date_str}")
    print(f"DEBUG: appointment_time_str = {appointment_time_str}")
    
    # Проверяем, что все необходимые данные есть
    if not doctor_id or not appointment_date_str or not appointment_time_str:
        messages.error(request, 'Недостаточно данных для записи. Пожалуйста, начните сначала.')
        return redirect('appointment_step1')
    
    # Получаем объекты из базы данных
    try:
        doctor = Doctor.objects.get(id=doctor_id, is_active=True)
    except Doctor.DoesNotExist:
        messages.error(request, 'Выбранный врач не найден или недоступен.')
        return redirect('appointment_step1')
    
    # Определяем услугу
    if service_id:
        try:
            service = Service.objects.get(id=service_id, is_active=True)
        except Service.DoesNotExist:
            messages.error(request, 'Выбранная услуга не найдена.')
            return redirect('appointment_step1')
    else:
        # Если услуга не выбрана, используем консультацию врача
        service, created = Service.objects.get_or_create(
            name=f"Консультация {doctor.specialization.name.lower()}",
            defaults={
                'price': doctor.consultation_price or 0,
                'duration': doctor.consultation_duration or 30,
                'category': 'consultation',
                'is_active': True,
            }
        )
    
    # Преобразуем дату и время
    try:
        appointment_datetime = datetime.strptime(
            f"{appointment_date_str} {appointment_time_str}",
            '%Y-%m-%d %H:%M:%S'
        )
        appointment_datetime = timezone.make_aware(appointment_datetime)
    except ValueError:
        messages.error(request, 'Некорректные дата или время.')
        return redirect('appointment_step4')
    
    # Проверяем, что выбранное время не в прошлом
    if appointment_datetime < timezone.now():
        messages.error(request, 'Нельзя записаться на прошедшее время.')
        return redirect('appointment_step4')
    
    # Получаем профиль пациента
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        messages.error(request, 'Пожалуйста, заполните профиль пациента.')
        return redirect('profile_edit')
    
    if request.method == 'POST':

        print(f"POST запрос получен")
        print(f"Данные: doctor_id={doctor_id}, service_id={service_id}")
        print(f"Дата: {appointment_date_str}, Время: {appointment_time_str}")

        try:
            # Получаем расписание врача на эту дату
            schedule = DoctorSchedule.objects.filter(
                doctor=doctor,
                date=appointment_datetime.date(),
                is_available=True,
                is_working_day=True
            ).first()
            
            if not schedule:
                # Если расписания нет, создаем его автоматически
                schedule = DoctorSchedule.objects.create(
                    doctor=doctor,
                    date=appointment_datetime.date(),
                    start_time='09:00',
                    end_time='18:00',
                    slot_duration=doctor.consultation_duration or 30,
                    is_available=True,
                    is_working_day=True,
                    room=f"Кабинет {random.randint(100, 500)}",  # Случайный кабинет
                )
                print(f"Создано расписание для врача {doctor.full_name()} на {appointment_datetime.date()}")
            
            # Проверяем, что время попадает в рабочие часы врача
            schedule_start = datetime.combine(appointment_datetime.date(), schedule.start_time)
            schedule_end = datetime.combine(appointment_datetime.date(), schedule.end_time)
            
            if timezone.is_naive(schedule_start):
                schedule_start = timezone.make_aware(schedule_start)
            if timezone.is_naive(schedule_end):
                schedule_end = timezone.make_aware(schedule_end)
            
            if not (schedule_start <= appointment_datetime <= schedule_end):
                messages.error(request, 'Выбранное время не входит в рабочие часы врача.')
                return redirect('appointment_step4')
            
            # Проверяем, не занят ли уже этот слот
            existing_appointment = Appointment.objects.filter(
                doctor=doctor,
                appointment_time__date=appointment_datetime.date(),
                appointment_time__hour=appointment_datetime.hour,
                appointment_time__minute=appointment_datetime.minute,
                status__in=['pending', 'confirmed']
            ).exists()
            
            if existing_appointment:
                messages.error(request, 'Это время уже занято. Пожалуйста, выберите другое время.')
                return redirect('appointment_step4')
            
            # Создаем запись
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                service=service,
                schedule=schedule,
                appointment_time=appointment_datetime,
                status='pending',
                created_by=request.user,
            )
            
            # Очищаем сессию
            session_keys_to_remove = [
                'appointment_doctor_id',
                'appointment_service_id', 
                'appointment_specialization_id',
                'appointment_date', 
                'appointment_time'
            ]
            
            for key in session_keys_to_remove:
                if key in request.session:
                    del request.session[key]
            
            # Сохраняем изменения сессии
            request.session.modified = True
            
            messages.success(
                request, 
                f'✅ Запись успешно создана! Номер записи: {appointment.appointment_number}. '
                f'Врач: {doctor.full_name()}. '
                f'Дата и время: {appointment_datetime.strftime("%d.%m.%Y %H:%M")}.'
            )
            
            return redirect('appointment_detail', pk=appointment.pk)

            print(f"Запись создана успешно: {appointment.id}")

        except Exception as e:
            # Логируем ошибку для отладки
            import traceback
            error_details = traceback.format_exc()
            print(f"Ошибка при создании записи: {e}")
            print(f"Детали ошибки: {error_details}")
            
            messages.error(
                request, 
                'Произошла ошибка при создании записи. '
                'Пожалуйста, попробуйте снова или свяжитесь с администрацией.'
            )
            return render(request, 'main/appointment/step5.html', context)
    
    # Если GET запрос - показываем страницу подтверждения
    context = {
        'title': 'Запись на прием - Подтверждение',
        'doctor': doctor,
        'service': service,
        'patient': patient,
        'appointment_datetime': appointment_datetime,
    }
    
    return render(request, 'main/appointment/step5.html', context)
    print(f"Ошибка: {e}")


def get_available_slots(request):
    """API для получения доступных слотов (AJAX)"""
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')
    
    if not doctor_id or not date_str:
        return JsonResponse({'error': 'Недостаточно данных'}, status=400)
    
    try:
        doctor = Doctor.objects.get(id=doctor_id)
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except (Doctor.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Некорректные данные'}, status=400)
    
    # Получаем расписание на выбранную дату
    schedule = DoctorSchedule.objects.filter(
        doctor=doctor,
        date=appointment_date,
        is_available=True,
        is_working_day=True
    ).first()
    
    if schedule:
        slots = schedule.get_available_slots()
        slots_str = [slot.strftime('%H:%M') for slot in slots]
        return JsonResponse({'slots': slots_str})
    else:
        return JsonResponse({'slots': []})


# ==================== ЛИЧНЫЙ КАБИНЕТ ====================

def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        user_form = PatientRegistrationForm(request.POST)
        if user_form.is_valid():
            user = user_form.save()
            
            # Автоматический вход после регистрации
            login(request, user)
            
            messages.success(request, 'Регистрация успешна! Заполните профиль пациента.')
            return redirect('profile_edit')
    else:
        user_form = PatientRegistrationForm()
    
    context = {
        'title': 'Регистрация',
        'form': user_form,
    }
    
    return render(request, 'main/auth/register.html', context)


@login_required
def profile(request):
    """Личный кабинет пациента"""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        messages.warning(request, 'Пожалуйста, заполните профиль пациента')
        return redirect('profile_edit')
    
    # Получаем активные записи
    active_appointments = Appointment.objects.filter(
        patient=patient,
        status__in=['pending', 'confirmed'],
        appointment_time__gte=timezone.now()
    ).order_by('appointment_time')
    
    # Получаем прошедшие записи
    past_appointments = Appointment.objects.filter(
        patient=patient,
        status__in=['completed', 'cancelled', 'no_show']
    ).order_by('-appointment_time')[:10]
    
    context = {
        'title': 'Личный кабинет',
        'patient': patient,
        'active_appointments': active_appointments,
        'past_appointments': past_appointments,
    }
    
    return render(request, 'main/profile/index.html', context)


@login_required
def profile_edit(request):
    """Редактирование профиля пациента"""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        patient = None
    
    if request.method == 'POST':
        form = PatientProfileForm(request.POST, instance=patient)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.user = request.user
            patient.save()
            
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = PatientProfileForm(instance=patient)
    
    context = {
        'title': 'Редактирование профиля',
        'form': form,
    }
    
    return render(request, 'main/profile/edit.html', context)


@login_required
def appointment_list(request):
    """Список записей пациента"""
    try:
        patient = Patient.objects.get(user=request.user)
    except Patient.DoesNotExist:
        messages.warning(request, 'Пожалуйста, заполните профиль пациента')
        return redirect('profile_edit')
    
    appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_time')
    
    context = {
        'title': 'Мои записи',
        'appointments': appointments,
    }
    
    return render(request, 'main/appointment/list.html', context)


@login_required
def appointment_detail(request, pk):
    """Детальная страница записи"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Проверяем, что запись принадлежит текущему пользователю
    if appointment.patient.user != request.user and not request.user.is_staff:
        messages.error(request, 'У вас нет доступа к этой записи')
        return redirect('appointment_list')
    
    context = {
        'title': f'Запись #{appointment.appointment_number}',
        'appointment': appointment,
    }
    
    return render(request, 'main/appointment/detail.html', context)


@login_required
def appointment_cancel(request, pk):
    """Отмена записи"""
    appointment = get_object_or_404(Appointment, pk=pk)
    
    # Проверяем, что запись принадлежит текущему пользователю
    if appointment.patient.user != request.user:
        messages.error(request, 'У вас нет доступа к этой записи')
        return redirect('appointment_list')
    
    if appointment.status not in ['pending', 'confirmed']:
        messages.error(request, 'Нельзя отменить эту запись')
        return redirect('appointment_detail', pk=appointment.pk)
    
    if request.method == 'POST':
        appointment.status = 'cancelled'
        appointment.save()
        
        messages.success(request, 'Запись успешно отменена')
        return redirect('appointment_list')
    
    context = {
        'title': 'Отмена записи',
        'appointment': appointment,
    }
    
    return render(request, 'main/appointment/cancel.html', context)


# ==================== ОТЗЫВЫ ====================

@login_required
def add_review(request, doctor_id):
    """Добавление отзыва о враче"""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    # Проверяем, был ли пациент у этого врача
    try:
        patient = Patient.objects.get(user=request.user)
        has_appointment = Appointment.objects.filter(
            patient=patient,
            doctor=doctor,
            status='completed'
        ).exists()
        
        if not has_appointment:
            messages.error(request, 'Вы можете оставить отзыв только после приема у врача')
            return redirect('doctor_detail', pk=doctor.pk)
    except Patient.DoesNotExist:
        messages.error(request, 'Пожалуйста, заполните профиль пациента')
        return redirect('profile_edit')
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.patient = patient
            review.doctor = doctor
            review.save()
            
            messages.success(request, 'Отзыв успешно отправлен на модерацию')
            return redirect('doctor_detail', pk=doctor.pk)
    else:
        form = ReviewForm()
    
    context = {
        'title': 'Добавить отзыв',
        'doctor': doctor,
        'form': form,
    }
    
    return render(request, 'main/reviews/add.html', context)


# ==================== НОВОСТИ ====================

class NewsListView(ListView):
    """Список новостей"""
    model = News
    template_name = 'main/news/list.html'
    context_object_name = 'news_list'
    paginate_by = 10
    
    def get_queryset(self):
        return News.objects.filter(
            is_published=True,
            published_at__lte=timezone.now()
        ).order_by('-published_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Новости'
        return context


class NewsDetailView(DetailView):
    """Детальная страница новости"""
    model = News
    template_name = 'main/news/detail.html'
    context_object_name = 'news'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.object.title
        
        # Получаем похожие новости
        similar_news = News.objects.filter(
            is_published=True,
            published_at__lte=timezone.now()
        ).exclude(
            id=self.object.id
        ).order_by('-published_at')[:3]
        
        context['similar_news'] = similar_news
        return context


# ==================== ПОИСК ====================

def search(request):
    """Поиск по сайту"""
    query = request.GET.get('q', '')
    results = []
    
    if query:
        # Поиск врачей
        doctors = Doctor.objects.filter(
            Q(last_name__icontains=query) |
            Q(first_name__icontains=query) |
            Q(middle_name__icontains=query) |
            Q(specialization__name__icontains=query) |
            Q(bio__icontains=query)
        ).filter(is_active=True)
        
        # Поиск услуг
        services = Service.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query)
        ).filter(is_active=True)
        
        # Поиск новостей
        news = News.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(excerpt__icontains=query)
        ).filter(is_published=True, published_at__lte=timezone.now())
        
        results = {
            'doctors': doctors,
            'services': services,
            'news': news,
        }
    
    context = {
        'title': 'Поиск',
        'query': query,
        'results': results,
    }
    
    return render(request, 'main/search.html', context)


# ==================== API ДЛЯ AJAX ====================

def api_doctor_schedule(request, doctor_id):
    """API для получения расписания врача"""
    try:
        doctor = Doctor.objects.get(id=doctor_id)
        
        # Получаем расписание на ближайшие 14 дней
        today = timezone.now().date()
        end_date = today + timedelta(days=14)
        
        schedule_data = []
        schedules = DoctorSchedule.objects.filter(
            doctor=doctor,
            date__range=[today, end_date],
            is_available=True,
            is_working_day=True
        ).order_by('date')
        
        for schedule in schedules:
            slots = schedule.get_available_slots()
            if slots:
                schedule_data.append({
                    'date': schedule.date.strftime('%Y-%m-%d'),
                    'slots': [slot.strftime('%H:%M') for slot in slots],
                })
        
        return JsonResponse({
            'doctor': {
                'id': doctor.id,
                'name': doctor.full_name(),
                'specialization': doctor.specialization.name,
            },
            'schedule': schedule_data,
        })
    
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Врач не найден'}, status=404)


def api_available_dates(request, doctor_id):
    """API для получения доступных дат врача"""
    try:
        doctor = Doctor.objects.get(id=doctor_id)
        
        # Получаем доступные даты на ближайшие 14 дней
        today = timezone.now().date()
        end_date = today + timedelta(days=14)
        
        available_dates = []
        for i in range(14):
            check_date = today + timedelta(days=i)
            
            schedule = DoctorSchedule.objects.filter(
                doctor=doctor,
                date=check_date,
                is_available=True,
                is_working_day=True
            ).first()
            
            if schedule and schedule.get_available_slots():
                available_dates.append(check_date.strftime('%Y-%m-%d'))
        
        return JsonResponse({'available_dates': available_dates})
    
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Врач не найден'}, status=404)


def logout_view(request):
    """Выход из системы с перенаправлением на главную"""
    auth_logout(request)
    return redirect('home')




def user_login(request):
    """Универсальный вход для всех пользователей (пациентов и врачей)"""
    if request.user.is_authenticated:
        return redirect(get_redirect_url(request.user))
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Определяем, куда перенаправить
            redirect_url = get_redirect_url(user)
            
            # Сообщение о успешном входе
            if is_doctor(user):
                messages.success(request, f'Добро пожаловать, доктор {user.doctor.full_name()}!')
            else:
                messages.success(request, f'Добро пожаловать, {user.get_full_name() or user.username}!')
            
            return redirect(redirect_url)
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    
    context = {
        'title': 'Вход в систему',
    }
    
    return render(request, 'main/auth/login.html', context)


def is_doctor(user):
    """Проверяет, является ли пользователь врачом"""
    if not user.is_authenticated:
        return False
    try:
        return Doctor.objects.filter(user=user).exists()
    except:
        return False


def get_redirect_url(user):
    """Определяет URL для перенаправления после входа"""
    if is_doctor(user):
        return 'doctor_dashboard'
    else:
        return 'profile'


@login_required
def user_dashboard(request):
    """Универсальный личный кабинет"""
    if is_doctor(request.user):
        return redirect('doctor_dashboard')
    else:
        return redirect('profile')
