from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Patient, Appointment, Review

class PatientRegistrationForm(UserCreationForm):
    """Форма регистрации пациента"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
        return user


class PatientProfileForm(forms.ModelForm):
    """Форма профиля пациента"""
    class Meta:
        model = Patient
        fields = [
            'birth_date', 'gender', 'insurance_policy', 
            'phone', 'address', 'blood_type',
            'allergies', 'chronic_diseases',
            'emergency_contact', 'emergency_phone'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'allergies': forms.Textarea(attrs={'rows': 2}),
            'chronic_diseases': forms.Textarea(attrs={'rows': 2}),
        }


class AppointmentForm(forms.ModelForm):
    """Форма записи на прием"""
    class Meta:
        model = Appointment
        fields = ['symptoms', 'notes']
        widgets = {
            'symptoms': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Опишите ваши симптомы или жалобы'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Дополнительная информация'
            }),
        }


class ReviewForm(forms.ModelForm):
    """Форма отзыва"""
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Опишите ваш опыт посещения врача'
            }),
        }


class DoctorLoginForm(AuthenticationForm):
    """Форма входа для врачей"""
    username = forms.CharField(
        label='Имя пользователя или Email',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите логин или email'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'})
    )
