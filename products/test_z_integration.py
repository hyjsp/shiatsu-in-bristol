import pytest
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, time
from products.models import Product, Category, Booking
from accounts.models import CustomUser
from conftest import created_event_ids
import uuid


class IntegrationBookingFlowTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(email='test@example.com', password='testpass123')

    def test_complete_booking_flow(self):
        # Clear all products and categories to ensure a clean slate
        Product.objects.all().delete()
        Category.objects.all().delete()
        # Create the required 'Shiatsu Sessions' category for BookingForm validation
        shiatsu_category = Category.objects.create(name='Shiatsu Sessions')
        # Create a unique category for this test (optional, but not used for the product)
        unique_category_name = f"Integration Category {uuid.uuid4().hex[:8]}"
        # integration_category = Category.objects.create(name=unique_category_name)
        product = Product.objects.create(
            name='Integration Test Session',
            description='A relaxing 60-minute session',
            price=65.00,
            duration_minutes=60,
            category=shiatsu_category,  # Use the required category
            is_active=True
        )
        # 1. User visits product list
        response = self.client.get(reverse('bookings:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Integration Test Session', response.content.decode())
        self.assertIn(f'href="/bookings/{product.pk}/"', response.content.decode())

        # 2. User clicks on product (simulated by visiting detail page)
        response = self.client.get(reverse('bookings:product_detail', args=[product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Book this session', response.content.decode())

        # 3. User submits booking form
        tomorrow = (timezone.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
        unique_notes = f'TEST_BOOKING_test_complete_booking_flow_{uuid.uuid4().hex[:8]}'
        booking_data = {
            'session_date': tomorrow,
            'session_time': '14:00',
            'notes': unique_notes
        }
        response = self.client.post(reverse('bookings:product_detail', args=[product.pk]), booking_data)
        self.assertEqual(response.status_code, 302)
        booking = Booking.objects.filter(notes=unique_notes).first()
        self.assertIsNotNone(booking)
        # Track event IDs for cleanup
        if hasattr(booking, 'google_calendar_event_id') and booking.google_calendar_event_id:
            created_event_ids.append(booking.google_calendar_event_id)
        if hasattr(booking, 'admin_calendar_event_id') and booking.admin_calendar_event_id:
            created_event_ids.append(booking.admin_calendar_event_id)
        # 4. Booking confirmation page
        response = self.client.get(reverse('bookings:booking_confirmation', args=[booking.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('Booking Confirmed', response.content.decode()) 