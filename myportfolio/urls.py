# myportfolio/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Админка Django
    path('admin/', admin.site.urls),
    
    # Приложение main (ваше основное приложение поликлиники)
    path('', include('main.urls')),
    
    # ✅ Аутентификация (Django встроенные views) - ОСТАВЬТЕ здесь
    path('login/', auth_views.LoginView.as_view(
        template_name='main/auth/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    
    path('logout/', auth_views.LogoutView.as_view(
        next_page='home'
    ), name='logout'),
]

# В режиме разработки добавляем маршруты для статических и медиа файлов
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)