from django import forms
from django.utils import timezone
from .models import Booking, Product, Category
from datetime import timedelta, datetime
from django.db.models import Q

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['session_date', 'session_time', 'notes']
        widgets = {
            'session_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'session_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Any notes or requests?'}),
        }

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product

    def clean(self):
        cleaned_data = super().clean()
        session_date = cleaned_data.get('session_date')
        session_time = cleaned_data.get('session_time')
        if session_date and session_time:
            product = self.product
            if not product:
                raise forms.ValidationError("Product is required for booking.")
            # Get the 'Shiatsu Sessions' category
            try:
                shiatsu_category = Category.objects.get(name__iexact='Shiatsu Sessions')
            except Category.DoesNotExist:
                raise forms.ValidationError("Shiatsu Sessions category does not exist.")
            shiatsu_products = Product.objects.filter(category=shiatsu_category)
            from datetime import datetime, timedelta
            session_start = datetime.combine(session_date, session_time)
            duration = product.duration_minutes or 60
            session_end = session_start + timedelta(minutes=duration)
            now = timezone.now()
            session_datetime = timezone.make_aware(session_start)
            if session_datetime < now + timedelta(hours=24):
                raise forms.ValidationError("Bookings must be made at least 24 hours in advance.")
            # Check for overlap with any other session in the category (exclude self for updates)
            existing_sessions = Booking.objects.filter(
                product__in=shiatsu_products,
                session_date=session_date,
                is_admin_slot=False
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            for other in existing_sessions:
                other_start = datetime.combine(other.session_date, other.session_time)
                other_duration = other.product.duration_minutes or 60
                other_end = other_start + timedelta(minutes=other_duration)
                if (session_start < other_end and session_end > other_start):
                    raise forms.ValidationError("Sorry, this time slot overlaps with another Shiatsu Session. Please choose another.")
            # Prevent overlap with 'Admin' slots
            admin_bookings = Booking.objects.filter(
                product__in=shiatsu_products,
                session_date=session_date,
                is_admin_slot=True
            )
            for admin_booking in admin_bookings:
                admin_start = datetime.combine(admin_booking.session_date, admin_booking.session_time)
                admin_end = admin_start + timedelta(minutes=30)
                if (session_start < admin_end and session_end > admin_start):
                    raise forms.ValidationError("This session conflicts with an Admin slot. Please choose another time.")
            # Prevent booking an admin slot that would overlap with an existing session
            if cleaned_data.get('is_admin_slot') or (hasattr(self.instance, 'is_admin_slot') and self.instance.is_admin_slot):
                session_bookings = Booking.objects.filter(
                    product__in=shiatsu_products,
                    session_date=session_date,
                    is_admin_slot=False
                )
                admin_start = session_start
                admin_end = admin_start + timedelta(minutes=30)
                for session_booking in session_bookings:
                    s_start = datetime.combine(session_booking.session_date, session_booking.session_time)
                    s_end = s_start + timedelta(minutes=session_booking.product.duration_minutes or 60)
                    if (admin_start < s_end and admin_end > s_start):
                        raise forms.ValidationError("Admin slot conflicts with an existing session. Please choose another time.")
        return cleaned_data

    def clean_session_date(self):
        session_date = self.cleaned_data['session_date']
        today = timezone.now().date()
        now = timezone.now()
        # Prevent booking in the past
        if session_date < today:
            raise forms.ValidationError("Session date cannot be in the past.")
        return session_date

    def clean_notes(self):
        import bleach
        notes = self.cleaned_data.get('notes', '')
        # Remove all HTML tags and attributes
        notes = bleach.clean(notes, tags=[], attributes={}, strip=True)
        max_length = 1000
        if len(notes) > max_length:
            raise forms.ValidationError(f"Notes cannot exceed {max_length} characters.")
        return notes 