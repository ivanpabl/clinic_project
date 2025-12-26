# main/urls.py - ДОБАВЬТЕ этот импорт в начале файла
from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    # Главная и статические страницы
    path('', views.home, name='home'),
    path('about/', views.about_clinic, name='about'),
    path('contacts/', views.contacts, name='contacts'),
    
    # Врачи
    path('doctors/', views.DoctorListView.as_view(), name='doctors_list'),
    path('doctors/<int:pk>/', views.DoctorDetailView.as_view(), name='doctor_detail'),
    path('doctor/login/', views.doctor_login, name='doctor_login'),
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/schedule/', views.doctor_schedule, name='doctor_schedule'),
    path('doctor/schedule/day/<str:date_str>/', views.doctor_schedule_day, name='doctor_schedule_day'),
    path('doctor/schedule/working/', views.doctor_working_schedule, name='doctor_working_schedule'),
    path('doctor/appointment/<int:pk>/', views.doctor_appointment_detail, name='doctor_appointment_detail'),
    path('doctor/statistics/', views.doctor_statistics, name='doctor_statistics'),
    
    # Услуги
    path('services/', views.ServiceListView.as_view(), name='services_list'),
    path('services/<int:pk>/', views.ServiceDetailView.as_view(), name='service_detail'),
    
    # Запись на прием
    path('appointment/step1/', views.appointment_step1, name='appointment_step1'),
    path('appointment/step2/', views.appointment_step2, name='appointment_step2'),
    path('appointment/step2/<int:service_id>/', views.appointment_step2, name='appointment_step2_service'),
    path('appointment/doctors/', views.appointment_step2_doctors, name='appointment_step2_doctors'),
    path('appointment/step3/', views.appointment_step3, name='appointment_step3'),
    path('appointment/step4/', views.appointment_step4, name='appointment_step4'),
    path('appointment/step5/', views.appointment_step5, name='appointment_step5'),
    path('appointment/slots/', views.get_available_slots, name='get_available_slots'),
    
    # Личный кабинет
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:pk>/cancel/', views.appointment_cancel, name='appointment_cancel'),
    
    # Отзывы
    path('doctors/<int:doctor_id>/review/', views.add_review, name='add_review'),
    
    # Новости
    path('news/', views.NewsListView.as_view(), name='news_list'),
    path('news/<int:pk>/', views.NewsDetailView.as_view(), name='news_detail'),
    
    # Поиск
    path('search/', views.search, name='search'),
    
    # API
    path('api/doctor/<int:doctor_id>/schedule/', views.api_doctor_schedule, name='api_doctor_schedule'),
    path('api/doctor/<int:doctor_id>/available-dates/', views.api_available_dates, name='api_available_dates'),
    
    path('login/', auth_views.LoginView.as_view(template_name='main/auth/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),



    path('dashboard/', views.user_dashboard, name='dashboard'),
]