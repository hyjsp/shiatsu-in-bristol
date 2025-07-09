from django import forms
from django.utils import timezone
from .models import Booking

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['session_date', 'session_time', 'notes']
        widgets = {
            'session_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'session_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any notes or requests?'}),
        }

    def clean_session_date(self):
        session_date = self.cleaned_data['session_date']
        if session_date < timezone.now().date():
            raise forms.ValidationError("Session date cannot be in the past.")
        return session_date 