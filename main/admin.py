from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import (
    Specialization, Department, Doctor, Service, 
    DoctorSchedule, Patient, Appointment, Review,
    News, Contact, Slider
)

# Inline для расписания врача
class DoctorScheduleInline(admin.TabularInline):
    model = DoctorSchedule
    extra = 1
    fields = ('date', 'start_time', 'end_time', 'is_available', 'room')

# Inline для услуг врача
class ServiceDoctorsInline(admin.TabularInline):
    model = Service.doctors.through
    extra = 1
    verbose_name = "Услуга врача"
    verbose_name_plural = "Услуги врача"

@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'doctor_count')
    search_fields = ('name',)
    
    def doctor_count(self, obj):
        return obj.doctor_set.count()
    doctor_count.short_description = 'Количество врачей'

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'floor', 'phone', 'doctor_count')
    list_filter = ('floor',)
    search_fields = ('name', 'phone')
    
    def doctor_count(self, obj):
        return obj.doctor_set.count()
    doctor_count.short_description = 'Количество врачей'

# main/admin.py - исправленная версия DoctorAdmin

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'specialization', 'department', 'category', 
                   'experience', 'is_active', 'photo_preview')
    list_filter = ('specialization', 'department', 'category', 'is_active')
    search_fields = ('last_name', 'first_name', 'middle_name', 'specialization__name')
    
    # УДАЛИТЕ эту строку, если services - не ManyToManyField:
    # filter_horizontal = ('services',)  # ← удалите или закомментируйте
    
    # Вместо этого можно использовать filter_horizontal только для ManyToMany полей:
    filter_horizontal = ()  # если у вас нет ManyToMany полей
    
    # ИЛИ если у вас есть ManyToMany поле (например, 'specialties'):
    # filter_horizontal = ('specialties',)  # только для ManyToManyField
    
    readonly_fields = ('photo_preview', 'created_at')
    inlines = [DoctorScheduleInline]
    
    fieldsets = (
        ('Личная информация', {
            'fields': ('last_name', 'first_name', 'middle_name', 'photo', 'photo_preview')
        }),
        ('Профессиональная информация', {
            'fields': ('specialization', 'department', 'category', 'experience')
        }),
        ('Образование и квалификация', {
            'fields': ('education', 'qualifications', 'bio')
        }),
        ('Контактная информация', {
            'fields': ('phone', 'email')
        }),
        ('Рабочие параметры', {
            'fields': ('is_active', 'consultation_duration', 'consultation_price')
        }),
        ('Метаданные', {
            'fields': ('order', 'created_at')
        }),
    )
    
    def photo_preview(self, obj):
        if obj.photo:
            return mark_safe(f'<img src="{obj.photo.url}" style="max-height: 100px;" />')
        return "Нет фото"
    photo_preview.short_description = 'Превью фото'

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'duration', 'is_active', 'is_free')
    list_filter = ('category', 'is_active', 'is_free')
    search_fields = ('name', 'description')
    filter_horizontal = ('doctors',)
    inlines = [ServiceDoctorsInline]

@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'start_time', 'end_time', 'is_available', 'room')
    list_filter = ('doctor', 'date', 'is_available')
    search_fields = ('doctor__last_name', 'doctor__first_name', 'room')
    date_hierarchy = 'date'

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('user', 'birth_date', 'gender', 'insurance_policy', 'phone', 'created_at')
    list_filter = ('gender', 'created_at')
    search_fields = ('user__last_name', 'user__first_name', 'insurance_policy', 'phone')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Личная информация', {
            'fields': ('user', 'birth_date', 'gender')
        }),
        ('Медицинская информация', {
            'fields': ('insurance_policy', 'blood_type', 'allergies', 'chronic_diseases')
        }),
        ('Контактная информация', {
            'fields': ('phone', 'address', 'emergency_contact', 'emergency_phone')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('appointment_number', 'patient', 'doctor', 'appointment_time', 
                   'status', 'service', 'created_at')
    list_filter = ('status', 'doctor', 'appointment_time', 'created_at')
    search_fields = ('appointment_number', 'patient__user__last_name', 
                    'doctor__last_name', 'symptoms')
    readonly_fields = ('appointment_number', 'created_at', 'updated_at')
    date_hierarchy = 'appointment_time'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('appointment_number', 'patient', 'doctor', 'service')
        }),
        ('Время приема', {
            'fields': ('schedule', 'appointment_time')
        }),
        ('Информация о записи', {
            'fields': ('status', 'symptoms', 'notes')
        }),
        ('Метаданные', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'rating', 'is_published', 'created_at')
    list_filter = ('rating', 'is_published', 'created_at')
    search_fields = ('patient__user__last_name', 'doctor__last_name', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient', 'doctor')

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'is_published', 'published_at', 'created_at')
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'image')
        }),
        ('Публикация', {
            'fields': ('author', 'is_published', 'published_at')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('type', 'value', 'description', 'order', 'is_active')
    list_filter = ('type', 'is_active')
    search_fields = ('value', 'description')
    list_editable = ('order', 'is_active')

@admin.register(Slider)
class SliderAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'image_preview')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'description')
    
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" style="max-height: 50px;" />')
        return "Нет изображения"
    image_preview.short_description = 'Превью'