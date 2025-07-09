import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import date, time, timedelta
from django.contrib.auth import get_user_model
from django import forms
from products.models import Category, Product
from products.forms import BookingForm

User = get_user_model()


class BookingFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Shiatsu Sessions')
        self.product = Product.objects.create(
            category=self.category,
            name='60-Minute Session',
            price=65.00,
            duration_minutes=60,
            is_active=True
        )

    def test_booking_form_valid_data(self):
        """Test that BookingForm accepts valid data"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        form_data = {
            'session_date': tomorrow,
            'session_time': '14:00',
            'notes': 'Test booking notes'
        }
        form = BookingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_booking_form_past_date_validation(self):
        """Test that BookingForm rejects past dates"""
        yesterday = timezone.now().date() - timedelta(days=1)
        form_data = {
            'session_date': yesterday,
            'session_time': '14:00',
            'notes': 'Test booking notes'
        }
        form = BookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Session date cannot be in the past', str(form.errors))

    def test_booking_form_today_date_validation(self):
        """Test that BookingForm accepts today's date"""
        today = timezone.now().date()
        form_data = {
            'session_date': today,
            'session_time': '14:00',
            'notes': 'Test booking notes'
        }
        form = BookingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_booking_form_future_date_validation(self):
        """Test that BookingForm accepts future dates"""
        future_date = timezone.now().date() + timedelta(days=7)
        form_data = {
            'session_date': future_date,
            'session_time': '14:00',
            'notes': 'Test booking notes'
        }
        form = BookingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_booking_form_required_fields(self):
        """Test that required fields are properly validated"""
        # Test missing session_date
        form_data = {
            'session_time': '14:00',
            'notes': 'Test booking notes'
        }
        form = BookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('session_date', form.errors)

        # Test missing session_time
        tomorrow = timezone.now().date() + timedelta(days=1)
        form_data = {
            'session_date': tomorrow,
            'notes': 'Test booking notes'
        }
        form = BookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('session_time', form.errors)

    def test_booking_form_optional_notes(self):
        """Test that notes field is optional"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        form_data = {
            'session_date': tomorrow,
            'session_time': '14:00'
        }
        form = BookingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_booking_form_widget_attributes(self):
        """Test that form widgets have correct attributes"""
        form = BookingForm()
        
        # Test session_date widget
        session_date_widget = form.fields['session_date'].widget
        self.assertIn('form-control', session_date_widget.attrs['class'])

        # Test session_time widget
        session_time_widget = form.fields['session_time'].widget
        self.assertIn('form-control', session_time_widget.attrs['class'])

        # Test notes widget
        notes_widget = form.fields['notes'].widget
        self.assertIn('form-control', notes_widget.attrs['class'])
        self.assertEqual(notes_widget.attrs['rows'], 3)
        self.assertEqual(notes_widget.attrs['placeholder'], 'Any notes or requests?')

    def test_booking_form_clean_session_date_method(self):
        """Test the custom clean_session_date method"""
        # Test past date
        past_date = timezone.now().date() - timedelta(days=1)
        form_data = {
            'session_date': past_date,
            'session_time': '14:00',
            'notes': 'Test booking'
        }
        form = BookingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Session date cannot be in the past', str(form.errors))

        # Test today's date
        today = timezone.now().date()
        form_data = {
            'session_date': today,
            'session_time': '14:00',
            'notes': 'Test booking'
        }
        form = BookingForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Test future date
        future_date = timezone.now().date() + timedelta(days=1)
        form_data = {
            'session_date': future_date,
            'session_time': '14:00',
            'notes': 'Test booking'
        }
        form = BookingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_booking_form_time_format_validation(self):
        """Test that time format is properly validated"""
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        # Test valid time format
        form_data = {
            'session_date': tomorrow,
            'session_time': '14:30',
            'notes': 'Test booking'
        }
        form = BookingForm(data=form_data)
        self.assertTrue(form.is_valid())

        # Test invalid time format
        form_data = {
            'session_date': tomorrow,
            'session_time': '25:00',  # Invalid hour
            'notes': 'Test booking'
        }
        form = BookingForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_booking_form_empty_data(self):
        """Test form with empty data"""
        form = BookingForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('session_date', form.errors)
        self.assertIn('session_time', form.errors)

    def test_booking_form_bound_vs_unbound(self):
        """Test bound vs unbound form behavior"""
        # Unbound form
        unbound_form = BookingForm()
        self.assertFalse(unbound_form.is_bound)
        
        # Bound form with data
        tomorrow = timezone.now().date() + timedelta(days=1)
        form_data = {
            'session_date': tomorrow,
            'session_time': '14:00',
            'notes': 'Test booking'
        }
        bound_form = BookingForm(data=form_data)
        self.assertTrue(bound_form.is_bound)

    def test_booking_form_field_order(self):
        """Test that form fields are in correct order"""
        form = BookingForm()
        field_names = list(form.fields.keys())
        expected_order = ['session_date', 'session_time', 'notes']
        self.assertEqual(field_names, expected_order) 