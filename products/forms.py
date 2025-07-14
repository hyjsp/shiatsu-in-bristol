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

    def clean(self):
        cleaned_data = super().clean()
        session_date = cleaned_data.get('session_date')
        session_time = cleaned_data.get('session_time')
        if session_date and session_time:
            qs = Booking.objects.filter(session_date=session_date, session_time=session_time)
            # Exclude self in case of update
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError("Sorry, this time slot is already booked. Please choose another.")
        return cleaned_data

    def clean_session_date(self):
        session_date = self.cleaned_data['session_date']
        if session_date < timezone.now().date():
            raise forms.ValidationError("Session date cannot be in the past.")
        return session_date 