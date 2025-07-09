import pytest
import threading
import time
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, time, timedelta
from products.models import Category, Product, Booking
from products.forms import BookingForm

User = get_user_model()


class BoundaryConditionTests(TestCase):
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

    def test_product_price_boundaries(self):
        """Test product price boundary conditions"""
        # Test minimum price (0.01)
        min_price_product = Product.objects.create(
            category=self.category,
            name='Minimum Price Session',
            price=0.01,
            duration_minutes=60,
            is_active=True
        )
        self.assertEqual(min_price_product.price, 0.01)
        
        # Test maximum reasonable price (9999.99)
        max_price_product = Product.objects.create(
            category=self.category,
            name='Maximum Price Session',
            price=9999.99,
            duration_minutes=60,
            is_active=True
        )
        self.assertEqual(max_price_product.price, 9999.99)
        
        # Test zero price (should be invalid)
        with self.assertRaises(ValidationError):
            Product.objects.create(
                category=self.category,
                name='Zero Price Session',
                price=0.00,
                duration_minutes=60,
                is_active=True
            )

    def test_product_duration_boundaries(self):
        """Test product duration boundary conditions"""
        # Test minimum duration (1 minute)
        min_duration_product = Product.objects.create(
            category=self.category,
            name='Minimum Duration Session',
            price=10.00,
            duration_minutes=1,
            is_active=True
        )
        self.assertEqual(min_duration_product.duration_minutes, 1)
        
        # Test maximum reasonable duration (480 minutes = 8 hours)
        max_duration_product = Product.objects.create(
            category=self.category,
            name='Maximum Duration Session',
            price=500.00,
            duration_minutes=480,
            is_active=True
        )
        self.assertEqual(max_duration_product.duration_minutes, 480)
        
        # Test zero duration (should be invalid)
        with self.assertRaises(ValidationError):
            Product.objects.create(
                category=self.category,
                name='Zero Duration Session',
                price=10.00,
                duration_minutes=0,
                is_active=True
            )

    def test_booking_date_boundaries(self):
        """Test booking date boundary conditions"""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Test booking for today (should be valid)
        today = timezone.now().date()
        today_data = {
            'session_date': today,
            'session_time': '14:00',
            'notes': 'Today booking'
        }
        
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            today_data
        )
        self.assertEqual(response.status_code, 302)  # Success
        
        # Test booking for yesterday (should be invalid)
        yesterday = today - timedelta(days=1)
        yesterday_data = {
            'session_date': yesterday,
            'session_time': '14:00',
            'notes': 'Yesterday booking'
        }
        
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            yesterday_data
        )
        self.assertEqual(response.status_code, 200)  # Stay on form with errors

    def test_booking_time_boundaries(self):
        """Test booking time boundary conditions"""
        self.client.login(email='test@example.com', password='testpass123')
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        # Test earliest time (00:00)
        early_data = {
            'session_date': tomorrow,
            'session_time': '00:00',
            'notes': 'Early morning booking'
        }
        
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            early_data
        )
        self.assertEqual(response.status_code, 302)  # Success
        
        # Test latest time (23:59)
        late_data = {
            'session_date': tomorrow,
            'session_time': '23:59',
            'notes': 'Late night booking'
        }
        
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            late_data
        )
        self.assertEqual(response.status_code, 302)  # Success

    def test_string_length_boundaries(self):
        """Test string field length boundaries"""
        # Test very long product name
        long_name = 'A' * 255  # Maximum length
        long_name_product = Product.objects.create(
            category=self.category,
            name=long_name,
            price=65.00,
            duration_minutes=60,
            is_active=True
        )
        self.assertEqual(long_name_product.name, long_name)
        
        # Test very long description
        long_description = 'B' * 1000
        long_desc_product = Product.objects.create(
            category=self.category,
            name='Long Description Session',
            description=long_description,
            price=65.00,
            duration_minutes=60,
            is_active=True
        )
        self.assertEqual(long_desc_product.description, long_description)


class ExtremeDataValueTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Shiatsu Sessions')

    def test_extreme_price_values(self):
        """Test extreme price values"""
        # Test very high price
        high_price_product = Product.objects.create(
            category=self.category,
            name='Expensive Session',
            price=999999.99,
            duration_minutes=60,
            is_active=True
        )
        self.assertEqual(high_price_product.price, 999999.99)
        
        # Test very small price
        small_price_product = Product.objects.create(
            category=self.category,
            name='Cheap Session',
            price=0.01,
            duration_minutes=60,
            is_active=True
        )
        self.assertEqual(small_price_product.price, 0.01)

    def test_extreme_duration_values(self):
        """Test extreme duration values"""
        # Test very long session
        long_session = Product.objects.create(
            category=self.category,
            name='Marathon Session',
            price=1000.00,
            duration_minutes=1440,  # 24 hours
            is_active=True
        )
        self.assertEqual(long_session.duration_minutes, 1440)
        
        # Test very short session
        short_session = Product.objects.create(
            category=self.category,
            name='Quick Session',
            price=5.00,
            duration_minutes=1,
            is_active=True
        )
        self.assertEqual(short_session.duration_minutes, 1)

    def test_extreme_string_values(self):
        """Test extreme string values"""
        # Test empty strings
        empty_name_product = Product.objects.create(
            category=self.category,
            name='',  # Empty name
            price=65.00,
            duration_minutes=60,
            is_active=True
        )
        self.assertEqual(empty_name_product.name, '')
        
        # Test strings with special characters
        special_chars = '!@#$%^&*()_+-=[]{}|;:,.<>?'
        special_product = Product.objects.create(
            category=self.category,
            name=special_chars,
            price=65.00,
            duration_minutes=60,
            is_active=True
        )
        self.assertEqual(special_product.name, special_chars)

    def test_extreme_unicode_values(self):
        """Test extreme unicode values"""
        # Test unicode characters
        unicode_name = 'Sesión con ñ y áéíóú 🧘‍♀️'
        unicode_product = Product.objects.create(
            category=self.category,
            name=unicode_name,
            price=65.00,
            duration_minutes=60,
            is_active=True
        )
        self.assertEqual(unicode_product.name, unicode_name)


class ConcurrentOperationTests(TestCase):
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

    def test_concurrent_booking_creation(self):
        """Test concurrent booking creation"""
        self.client.login(email='test@example.com', password='testpass123')
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        booking_data = {
            'session_date': tomorrow,
            'session_time': '14:00',
            'notes': 'Concurrent booking'
        }
        
        # Simulate concurrent requests
        def create_booking():
            response = self.client.post(
                reverse('products:product_detail', args=[self.product.pk]),
                booking_data
            )
            return response.status_code
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_booking)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that all bookings were created successfully
        bookings = Booking.objects.filter(notes='Concurrent booking')
        self.assertEqual(bookings.count(), 5)

    def test_concurrent_product_updates(self):
        """Test concurrent product updates"""
        # Simulate concurrent product updates
        def update_product():
            product = Product.objects.get(pk=self.product.pk)
            product.price += 1.00
            product.save()
            return product.price
        
        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=update_product)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check that product was updated
        self.product.refresh_from_db()
        self.assertEqual(self.product.price, 68.00)  # 65 + 3

    def test_concurrent_user_operations(self):
        """Test concurrent user operations"""
        # Simulate concurrent user logins
        def user_login():
            client = Client()
            success = client.login(email='test@example.com', password='testpass123')
            return success
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=user_login)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All logins should succeed
        # (This test mainly checks that concurrent logins don't crash the system)


class UnusualUserScenarioTests(TestCase):
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

    def test_user_with_multiple_bookings_same_time(self):
        """Test user creating multiple bookings for the same time"""
        self.client.login(email='test@example.com', password='testpass123')
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        # Create first booking
        booking1_data = {
            'session_date': tomorrow,
            'session_time': '14:00',
            'notes': 'First booking'
        }
        response1 = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            booking1_data
        )
        self.assertEqual(response1.status_code, 302)  # Success
        
        # Try to create second booking for same time
        booking2_data = {
            'session_date': tomorrow,
            'session_time': '14:00',
            'notes': 'Second booking'
        }
        response2 = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            booking2_data
        )
        self.assertEqual(response2.status_code, 200)  # Stay on form with errors
        
        # Check that only one booking was created
        bookings = Booking.objects.filter(
            user=self.user,
            session_date=tomorrow,
            session_time=time(14, 0)
        )
        self.assertEqual(bookings.count(), 1)

    def test_user_with_very_long_notes(self):
        """Test user entering very long booking notes"""
        self.client.login(email='test@example.com', password='testpass123')
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        long_notes = 'A' * 10000  # Very long notes
        
        booking_data = {
            'session_date': tomorrow,
            'session_time': '14:00',
            'notes': long_notes
        }
        
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            booking_data
        )
        self.assertEqual(response.status_code, 302)  # Success
        
        # Check that booking was created with long notes
        booking = Booking.objects.filter(notes=long_notes).first()
        self.assertIsNotNone(booking)
        self.assertEqual(len(booking.notes), 10000)

    def test_user_with_special_characters_in_notes(self):
        """Test user entering special characters in notes"""
        self.client.login(email='test@example.com', password='testpass123')
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        special_notes = 'Notes with "quotes", <tags>, & symbols, and emojis 🧘‍♀️'
        
        booking_data = {
            'session_date': tomorrow,
            'session_time': '14:00',
            'notes': special_notes
        }
        
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            booking_data
        )
        self.assertEqual(response.status_code, 302)  # Success
        
        # Check that booking was created with special characters
        booking = Booking.objects.filter(notes=special_notes).first()
        self.assertIsNotNone(booking)

    def test_user_booking_far_future_date(self):
        """Test user booking for a date far in the future"""
        self.client.login(email='test@example.com', password='testpass123')
        
        far_future = timezone.now().date() + timedelta(days=365)  # One year from now
        
        booking_data = {
            'session_date': far_future,
            'session_time': '14:00',
            'notes': 'Far future booking'
        }
        
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            booking_data
        )
        self.assertEqual(response.status_code, 302)  # Success
        
        # Check that booking was created
        booking = Booking.objects.filter(notes='Far future booking').first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.session_date, far_future)

    def test_user_with_inactive_product_booking(self):
        """Test user trying to book inactive product"""
        # Deactivate the product
        self.product.is_active = False
        self.product.save()
        
        self.client.login(email='test@example.com', password='testpass123')
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        booking_data = {
            'session_date': tomorrow,
            'session_time': '14:00',
            'notes': 'Inactive product booking'
        }
        
        # Try to access product detail page
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 404)  # Not found
        
        # Try to post booking data
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            booking_data
        )
        self.assertEqual(response.status_code, 404)  # Not found

    def test_user_with_deleted_product_booking(self):
        """Test user trying to book deleted product"""
        product_id = self.product.pk
        
        # Delete the product
        self.product.delete()
        
        self.client.login(email='test@example.com', password='testpass123')
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        booking_data = {
            'session_date': tomorrow,
            'session_time': '14:00',
            'notes': 'Deleted product booking'
        }
        
        # Try to access product detail page
        response = self.client.get(reverse('products:product_detail', args=[product_id]))
        self.assertEqual(response.status_code, 404)  # Not found
        
        # Try to post booking data
        response = self.client.post(
            reverse('products:product_detail', args=[product_id]),
            booking_data
        )
        self.assertEqual(response.status_code, 404)  # Not found


class DataValidationEdgeCases(TestCase):
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

    def test_form_validation_with_empty_data(self):
        """Test form validation with completely empty data"""
        self.client.login(email='test@example.com', password='testpass123')
        
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            {}
        )
        self.assertEqual(response.status_code, 200)  # Stay on form with errors

    def test_form_validation_with_none_values(self):
        """Test form validation with None values"""
        self.client.login(email='test@example.com', password='testpass123')
        
        booking_data = {
            'session_date': None,
            'session_time': None,
            'notes': None
        }
        
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            booking_data
        )
        self.assertEqual(response.status_code, 200)  # Stay on form with errors

    def test_form_validation_with_whitespace_only(self):
        """Test form validation with whitespace-only values"""
        self.client.login(email='test@example.com', password='testpass123')
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        booking_data = {
            'session_date': tomorrow,
            'session_time': '14:00',
            'notes': '   '  # Whitespace only
        }
        
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            booking_data
        )
        self.assertEqual(response.status_code, 302)  # Success (whitespace is trimmed)

    def test_form_validation_with_very_large_numbers(self):
        """Test form validation with very large numbers"""
        self.client.login(email='test@example.com', password='testpass123')
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        booking_data = {
            'session_date': tomorrow,
            'session_time': '25:00',  # Invalid hour
            'notes': 'Test booking'
        }
        
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            booking_data
        )
        self.assertEqual(response.status_code, 200)  # Stay on form with errors 