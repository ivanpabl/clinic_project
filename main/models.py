from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import time, datetime

# Модель для специализации врача
class Specialization(models.Model):
    """Специализации врачей"""
    name = models.CharField(max_length=100, verbose_name='Название специализации')
    description = models.TextField(blank=True, verbose_name='Описание')
    
    class Meta:
        verbose_name = 'Специализация'
        verbose_name_plural = 'Специализации'
        ordering = ['name']
    
    def __str__(self):
        return self.name


# Модель для отделения/кафедры
class Department(models.Model):
    """Отделения поликлиники"""
    name = models.CharField(max_length=200, verbose_name='Название отделения')
    description = models.TextField(blank=True, verbose_name='Описание отделения')
    floor = models.IntegerField(verbose_name='Этаж')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон отделения')
    
    class Meta:
        verbose_name = 'Отделение'
        verbose_name_plural = 'Отделения'
        ordering = ['name']
    
    def __str__(self):
        return self.name


# Модель врача
class Doctor(models.Model):
    """Врачи поликлиники"""
    # Личная информация
    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                verbose_name='Пользователь (аккаунт)')
    first_name = models.CharField(max_length=50, verbose_name='Имя')
    last_name = models.CharField(max_length=50, verbose_name='Фамилия')
    middle_name = models.CharField(max_length=50, blank=True, verbose_name='Отчество')
    
    # Профессиональная информация
    specialization = models.ForeignKey(Specialization, on_delete=models.PROTECT, 
                                       verbose_name='Специализация')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, 
                                   blank=True, verbose_name='Отделение')
    
    # Квалификация
    CATEGORY_CHOICES = [
        ('none', 'Без категории'),
        ('second', 'Вторая категория'),
        ('first', 'Первая категория'),
        ('highest', 'Высшая категория'),
    ]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, 
                                default='none', verbose_name='Категория')
    experience = models.IntegerField(verbose_name='Стаж работы (лет)')
    education = models.TextField(verbose_name='Образование')
    qualifications = models.TextField(blank=True, verbose_name='Квалификации и курсы')
    
    # Контактная информация
    phone = models.CharField(max_length=20, blank=True, verbose_name='Контактный телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    
    # Визуальное представление
    photo = models.ImageField(upload_to='doctors/', blank=True, null=True, 
                              verbose_name='Фотография')
    bio = models.TextField(blank=True, verbose_name='Краткая биография')
    
    # Рабочие параметры
    is_active = models.BooleanField(default=True, verbose_name='Принимает пациентов')
    consultation_duration = models.IntegerField(default=30, 
                                                verbose_name='Длительность приема (минут)')
    consultation_price = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                             verbose_name='Стоимость консультации')
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    order = models.IntegerField(default=0, verbose_name='Порядок отображения')
    
    class Meta:
        verbose_name = 'Врач'
        verbose_name_plural = 'Врачи'
        ordering = ['order', 'last_name', 'first_name']
    
    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}"
    
    def full_name(self):
        """Полное ФИО врача"""
        return f"{self.last_name} {self.first_name} {self.middle_name}"
    
    def short_name(self):
        """Сокращенное ФИО (Иванов И.И.)"""
        return f"{self.last_name} {self.first_name[0]}.{self.middle_name[0]}." if self.middle_name else f"{self.last_name} {self.first_name[0]}."
    
    def get_available_slots(self, date):
        """Получить доступные слоты на указанную дату"""
        from datetime import date as date_type
        if isinstance(date, date_type):
            date = timezone.make_aware(datetime.combine(date, time.min))
        
        # Получаем расписание врача на указанную дату
        schedule = self.schedules.filter(date=date, is_available=True).first()
        if schedule:
            return schedule.get_available_slots()
        return []
    
    @property
    def rating(self):
        """Средний рейтинг врача"""
        reviews = self.reviews.filter(is_published=True)
        if reviews.exists():
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return 0

    def is_doctor_user(self):
        """Проверяет, является ли пользователь врачом"""
        return hasattr(self, 'user') and self.user is not None
    
    def get_user_type(self):
        """Возвращает тип пользователя"""
        return 'doctor'


# Модель услуги
class Service(models.Model):
    """Медицинские услуги поликлиники"""
    SERVICE_CATEGORIES = [
        ('consultation', 'Консультация'),
        ('diagnostics', 'Диагностика'),
        ('treatment', 'Лечение'),
        ('analysis', 'Анализы'),
        ('procedure', 'Процедура'),
    ]
    
    name = models.CharField(max_length=200, verbose_name='Название услуги')
    category = models.CharField(max_length=20, choices=SERVICE_CATEGORIES, 
                                default='consultation', verbose_name='Категория')
    description = models.TextField(verbose_name='Описание услуги')
    short_description = models.CharField(max_length=300, blank=True, 
                                         verbose_name='Краткое описание')
    
    # Стоимость
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Стоимость')
    is_free = models.BooleanField(default=False, verbose_name='Бесплатная услуга')
    
    # Время и врачи
    duration = models.IntegerField(default=30, verbose_name='Длительность (минут)')
    doctors = models.ManyToManyField(Doctor, related_name='services', 
                                     blank=True, verbose_name='Врачи, оказывающие услугу')
    
    # Визуальное представление
    icon = models.CharField(max_length=50, blank=True, 
                            verbose_name='Иконка (например, fas fa-stethoscope)')
    image = models.ImageField(upload_to='services/', blank=True, null=True, 
                              verbose_name='Изображение')
    
    # Метаданные
    is_active = models.BooleanField(default=True, verbose_name='Активная услуга')
    order = models.IntegerField(default=0, verbose_name='Порядок отображения')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    
    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


# Модель расписания врача
class DoctorSchedule(models.Model):
    """Расписание врача на конкретный день"""
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, 
                               related_name='schedules', verbose_name='Врач')
    date = models.DateField(verbose_name='Дата приема')
    
    # Время работы
    start_time = models.TimeField(verbose_name='Время начала приема')
    end_time = models.TimeField(verbose_name='Время окончания приема')
    
    # Настройки
    slot_duration = models.IntegerField(default=30, verbose_name='Длительность слота (минут)')
    break_start = models.TimeField(null=True, blank=True, verbose_name='Начало перерыва')
    break_end = models.TimeField(null=True, blank=True, verbose_name='Конец перерыва')
    
    # Статус
    is_available = models.BooleanField(default=True, verbose_name='Прием ведется')
    is_working_day = models.BooleanField(default=True, verbose_name='Рабочий день')
    
    # Дополнительная информация
    room = models.CharField(max_length=20, blank=True, verbose_name='Кабинет')
    notes = models.TextField(blank=True, verbose_name='Примечания')
    
    class Meta:
        verbose_name = 'Расписание врача'
        verbose_name_plural = 'Расписания врачей'
        ordering = ['date', 'start_time']
        unique_together = ['doctor', 'date']
    
    def __str__(self):
        return f"{self.doctor} - {self.date}"
    
    def get_available_slots(self):
        """Генерирует список доступных временных слотов"""
        import datetime
        from django.utils import timezone
        
        slots = []
        current_time = datetime.datetime.combine(self.date, self.start_time)
        end_datetime = datetime.datetime.combine(self.date, self.end_time)
        
        # Преобразуем в aware datetime если нужно
        if timezone.is_naive(current_time):
            current_time = timezone.make_aware(current_time)
        if timezone.is_naive(end_datetime):
            end_datetime = timezone.make_aware(end_datetime)
        
        # Проверяем перерыв
        break_start_dt = None
        break_end_dt = None
        if self.break_start and self.break_end:
            break_start_dt = datetime.datetime.combine(self.date, self.break_start)
            break_end_dt = datetime.datetime.combine(self.date, self.break_end)
            if timezone.is_naive(break_start_dt):
                break_start_dt = timezone.make_aware(break_start_dt)
            if timezone.is_naive(break_end_dt):
                break_end_dt = timezone.make_aware(break_end_dt)
        
        slot_duration = datetime.timedelta(minutes=self.slot_duration)
        
        while current_time + slot_duration <= end_datetime:
            # Проверяем, не попадает ли слот в перерыв
            in_break = False
            if break_start_dt and break_end_dt:
                if break_start_dt <= current_time < break_end_dt:
                    in_break = True
            
            # Проверяем, не занят ли слот
            is_booked = self.appointments.filter(
                appointment_time__gte=current_time,
                appointment_time__lt=current_time + slot_duration,
                status__in=['confirmed', 'pending']
            ).exists()
            
            if not in_break and not is_booked:
                slots.append(current_time.time())
            
            current_time += slot_duration
        
        return slots
    
    @property
    def is_past(self):
        """Проверяет, прошла ли дата расписания"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.date < today


# Модель пациента (расширение User)
class Patient(models.Model):
    """Пациент - расширение стандартной модели User"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    
    # Личная информация
    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
    ]
    
    birth_date = models.DateField(verbose_name='Дата рождения')
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='Пол')
    
    # Медицинская информация
    insurance_policy = models.CharField(max_length=20, unique=True, 
                                        verbose_name='Номер полиса ОМС')
    blood_type = models.CharField(max_length=5, blank=True, verbose_name='Группа крови')
    allergies = models.TextField(blank=True, verbose_name='Аллергии')
    chronic_diseases = models.TextField(blank=True, verbose_name='Хронические заболевания')
    
    # Контактная информация
    phone = models.CharField(max_length=20, verbose_name='Контактный телефон')
    address = models.TextField(verbose_name='Адрес проживания')
    emergency_contact = models.CharField(max_length=100, blank=True, 
                                         verbose_name='Контактное лицо (для экстренных случаев)')
    emergency_phone = models.CharField(max_length=20, blank=True, 
                                       verbose_name='Телефон экстренного контакта')
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Пациент'
        verbose_name_plural = 'Пациенты'
        ordering = ['user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.insurance_policy})"
    
    @property
    def age(self):
        """Возраст пациента"""
        from datetime import date
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
    
    def get_active_appointments(self):
        """Активные записи пациента"""
        return self.appointments.filter(status__in=['pending', 'confirmed'])
    
    def get_past_appointments(self):
        """Прошедшие записи пациента"""
        return self.appointments.filter(status='completed')


# Модель записи на прием
class Appointment(models.Model):
    """Запись пациента на прием к врачу"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждена'),
        ('cancelled', 'Отменена'),
        ('completed', 'Завершена'),
        ('no_show', 'Не явился'),
    ]
    
    # Основная информация
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, 
                                related_name='appointments', verbose_name='Пациент')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, 
                               related_name='appointments', verbose_name='Врач')
    service = models.ForeignKey(Service, on_delete=models.PROTECT, 
                                verbose_name='Услуга')
    
    # Время приема
    schedule = models.ForeignKey(DoctorSchedule, on_delete=models.CASCADE, 
                                 related_name='appointments', verbose_name='Расписание')
    appointment_time = models.DateTimeField(verbose_name='Дата и время приема')
    
    # Статус и информация
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                              default='pending', verbose_name='Статус записи')
    symptoms = models.TextField(blank=True, verbose_name='Симптомы/жалобы')
    notes = models.TextField(blank=True, verbose_name='Примечания пациента')
    
    # Административная информация
    appointment_number = models.CharField(max_length=20, unique=True, 
                                          verbose_name='Номер записи')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                   verbose_name='Создана пользователем')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Запись на прием'
        verbose_name_plural = 'Записи на прием'
        ordering = ['-appointment_time']
    
    def __str__(self):
        return f"Запись #{self.appointment_number}: {self.patient} -> {self.doctor}"
    
    def save(self, *args, **kwargs):
        """Автоматическая генерация номера записи при создании"""
        if not self.appointment_number:
            from datetime import datetime
            date_str = datetime.now().strftime('%Y%m%d')
            last_appointment = Appointment.objects.filter(
                appointment_number__startswith=f"APT-{date_str}-"
            ).order_by('-appointment_number').first()
            
            if last_appointment:
                last_num = int(last_appointment.appointment_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.appointment_number = f"APT-{date_str}-{new_num:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def is_upcoming(self):
        """Проверяет, предстоящая ли это запись"""
        from django.utils import timezone
        return self.appointment_time > timezone.now() and self.status in ['pending', 'confirmed']
    
    @property
    def duration(self):
        """Длительность приема"""
        return self.service.duration if self.service else self.doctor.consultation_duration


# Модель отзыва о враче
class Review(models.Model):
    """Отзывы пациентов о врачах"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, 
                                verbose_name='Пациент')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, 
                               related_name='reviews', verbose_name='Врач')
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, 
                                       null=True, blank=True, verbose_name='Запись на прием')
    
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='Оценка (1-5)'
    )
    comment = models.TextField(verbose_name='Текст отзыва')
    
    # Модерация
    is_published = models.BooleanField(default=False, verbose_name='Опубликован')
    moderated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     verbose_name='Проверил модератор')
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
        unique_together = ['patient', 'doctor', 'appointment']
    
    def __str__(self):
        return f"Отзыв от {self.patient} о {self.doctor}"


# Модель новости/статьи
class News(models.Model):
    """Новости и статьи поликлиники"""
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='URL-адрес')
    
    content = models.TextField(verbose_name='Содержание')
    excerpt = models.TextField(blank=True, verbose_name='Краткое описание')
    
    # Визуальное представление
    image = models.ImageField(upload_to='news/', blank=True, null=True, 
                              verbose_name='Изображение')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                               verbose_name='Автор')
    
    # Публикация
    is_published = models.BooleanField(default=False, verbose_name='Опубликовано')
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата публикации')
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    
    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-published_at', '-created_at']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Автоматическая установка даты публикации"""
        if self.is_published and not self.published_at:
            from django.utils import timezone
            self.published_at = timezone.now()
        elif not self.is_published:
            self.published_at = None
        super().save(*args, **kwargs)


# Модель контактов поликлиники
class Contact(models.Model):
    """Контактная информация поликлиники"""
    CONTACT_TYPES = [
        ('phone', 'Телефон'),
        ('email', 'Email'),
        ('address', 'Адрес'),
        ('working_hours', 'Режим работы'),
        ('social', 'Социальная сеть'),
    ]
    
    type = models.CharField(max_length=20, choices=CONTACT_TYPES, verbose_name='Тип контакта')
    value = models.CharField(max_length=200, verbose_name='Значение')
    description = models.CharField(max_length=200, blank=True, verbose_name='Описание')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Иконка')
    order = models.IntegerField(default=0, verbose_name='Порядок отображения')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    
    class Meta:
        verbose_name = 'Контакт'
        verbose_name_plural = 'Контакты'
        ordering = ['order', 'type']
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.value}"


# Модель слайдера/карусели на главной
class Slider(models.Model):
    """Слайдер для главной страницы"""
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    description = models.TextField(blank=True, verbose_name='Описание')
    image = models.ImageField(upload_to='slider/', verbose_name='Изображение')
    link = models.CharField(max_length=200, blank=True, verbose_name='Ссылка')
    link_text = models.CharField(max_length=50, blank=True, verbose_name='Текст ссылки')
    order = models.IntegerField(default=0, verbose_name='Порядок отображения')
    is_active = models.BooleanField(default=True, verbose_name='Активно')
    
    class Meta:
        verbose_name = 'Слайд'
        verbose_name_plural = 'Слайды'
        ordering = ['order']
    
    def __str__(self):
        return self.title