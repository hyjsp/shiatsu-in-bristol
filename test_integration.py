import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from datetime import date, time, timedelta
from products.models import Category, Product, Booking
from accounts.models import CustomUser

User = get_user_model()


class CrossAppIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Shiatsu Sessions')
        self.product = Product.objects.create(
            category=self.category,
            name='60-Minute Session',
            description='A relaxing 60-minute session',
            price=65.00,
            duration_minutes=60,
            is_active=True
        )

    def test_user_registration_to_booking_flow(self):
        """Test complete flow from user registration to booking"""
        # 1. User registers
        registration_data = {
            'email': 'newuser@example.com',
            'password1': 'newpass12345',
            'password2': 'newpass12345',
        }
        response = self.client.post(reverse('account_signup'), registration_data)
        self.assertEqual(response.status_code, 302)  # Redirect after signup
        
        # 2. User logs in
        login_success = self.client.login(email='newuser@example.com', password='newpass12345')
        self.assertTrue(login_success)
        
        # 3. User visits product list
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '60-Minute Session')
        
        # 4. User visits product detail
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Book this session')
        
        # 5. User creates a booking
        tomorrow = timezone.now().date() + timedelta(days=1)
        booking_data = {
            'session_date': tomorrow,
            'session_time': '14:00',
            'notes': 'Test booking from new user'
        }
        response = self.client.post(
            reverse('products:product_detail', args=[self.product.pk]),
            booking_data
        )
        self.assertEqual(response.status_code, 302)  # Redirect to confirmation
        
        # 6. Check that booking was created
        booking = Booking.objects.filter(user__email='newuser@example.com').first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.product, self.product)

    def test_admin_user_management_integration(self):
        """Test admin interface for managing users and their bookings"""
        # Create admin user
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        # Create regular user with booking
        regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='regularpass123'
        )
        booking = Booking.objects.create(
            product=self.product,
            user=regular_user,
            session_date=date(2024, 1, 15),
            session_time=time(14, 0),
            notes='Regular user booking'
        )
        
        # Admin logs in
        self.client.login(email='admin@example.com', password='adminpass123')
        
        # Admin can view users
        response = self.client.get(reverse('admin:accounts_customuser_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'regular@example.com')
        
        # Admin can view bookings
        response = self.client.get(reverse('admin:products_booking_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Regular user booking')
        
        # Admin can view products
        response = self.client.get(reverse('admin:products_product_changelist'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '60-Minute Session')

    def test_email_notifications_integration(self):
        """Test email notifications for password reset and other actions"""
        # Test password reset email
        response = self.client.post(reverse('account_reset_password'), {
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('test@example.com', mail.outbox[0].to)
        
        # Test that email contains reset link
        email_content = mail.outbox[0].body
        self.assertIn('password reset', email_content.lower())

    def test_session_management_integration(self):
        """Test session management across different views"""
        # User logs in
        login_success = self.client.login(email='test@example.com', password='testpass123')
        self.assertTrue(login_success)
        
        # User visits different pages and session persists
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        
        # User logs out
        response = self.client.get(reverse('account_logout'))
        self.assertEqual(response.status_code, 200)
        
        # Session is cleared
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_user_profile_integration(self):
        """Test user profile integration with bookings"""
        # Create booking for user
        booking = Booking.objects.create(
            product=self.product,
            user=self.user,
            session_date=date(2024, 1, 15),
            session_time=time(14, 0),
            notes='Test booking'
        )
        
        # User logs in
        self.client.login(email='test@example.com', password='testpass123')
        
        # User can view their booking confirmation
        response = self.client.get(reverse('products:booking_confirmation', args=[booking.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Booking Confirmed!')
        
        # User cannot view other users' bookings
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
        other_booking = Booking.objects.create(
            product=self.product,
            user=other_user,
            session_date=date(2024, 1, 16),
            session_time=time(15, 0),
            notes='Other user booking'
        )
        
        response = self.client.get(reverse('products:booking_confirmation', args=[other_booking.pk]))
        self.assertEqual(response.status_code, 404)


class DataConsistencyTests(TestCase):
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

    def test_user_deletion_cascades_to_bookings(self):
        """Test that user deletion properly cascades to bookings"""
        # Create booking
        booking = Booking.objects.create(
            product=self.product,
            user=self.user,
            session_date=date(2024, 1, 15),
            session_time=time(14, 0),
            notes='Test booking'
        )
        
        # Verify booking exists
        self.assertEqual(Booking.objects.count(), 1)
        
        # Delete user
        self.user.delete()
        
        # Verify booking is deleted
        self.assertEqual(Booking.objects.count(), 0)

    def test_product_deletion_cascades_to_bookings(self):
        """Test that product deletion properly cascades to bookings"""
        # Create booking
        booking = Booking.objects.create(
            product=self.product,
            user=self.user,
            session_date=date(2024, 1, 15),
            session_time=time(14, 0),
            notes='Test booking'
        )
        
        # Verify booking exists
        self.assertEqual(Booking.objects.count(), 1)
        
        # Delete product
        self.product.delete()
        
        # Verify booking is deleted
        self.assertEqual(Booking.objects.count(), 0)

    def test_category_deletion_cascades_to_products(self):
        """Test that category deletion properly cascades to products"""
        # Verify product exists
        self.assertEqual(Product.objects.count(), 1)
        
        # Delete category
        self.category.delete()
        
        # Verify product is deleted
        self.assertEqual(Product.objects.count(), 0)


class AuthenticationIntegrationTests(TestCase):
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

    def test_authentication_required_views(self):
        """Test that authentication is required for protected views"""
        # Test product detail without authentication
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test booking confirmation without authentication
        booking = Booking.objects.create(
            product=self.product,
            user=self.user,
            session_date=date(2024, 1, 15),
            session_time=time(14, 0),
            notes='Test booking'
        )
        response = self.client.get(reverse('products:booking_confirmation', args=[booking.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_authentication_works_across_apps(self):
        """Test that authentication works consistently across all apps"""
        # Login
        self.client.login(email='test@example.com', password='testpass123')
        
        # Test access to different apps
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)

    def test_logout_clears_session_across_apps(self):
        """Test that logout clears session across all apps"""
        # Login
        self.client.login(email='test@example.com', password='testpass123')
        
        # Verify logged in
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Logout
        self.client.logout()
        
        # Verify logged out across apps
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 302)  # Redirect to login


class EmailIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_password_reset_email_integration(self):
        """Test password reset email functionality"""
        # Clear mail outbox
        mail.outbox.clear()
        
        # Request password reset
        response = self.client.post(reverse('account_reset_password'), {
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('test@example.com', mail.outbox[0].to)
        
        # Verify email content
        email = mail.outbox[0]
        self.assertIn('password reset', email.subject.lower())

    def test_email_backend_configuration(self):
        """Test that email backend is properly configured"""
        # Test that emails can be sent
        from django.core.mail import send_mail
        
        send_mail(
            'Test Subject',
            'Test Message',
            'from@example.com',
            ['to@example.com'],
            fail_silently=False,
        )
        
        # Verify email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Test Subject')


class AdminIntegrationTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='regularpass123'
        )
        self.category = Category.objects.create(name='Shiatsu Sessions')
        self.product = Product.objects.create(
            category=self.category,
            name='60-Minute Session',
            price=65.00,
            duration_minutes=60,
            is_active=True
        )

    def test_admin_can_manage_all_models(self):
        """Test that admin can manage all models across apps"""
        self.client.login(email='admin@example.com', password='adminpass123')
        
        # Test user management
        response = self.client.get(reverse('admin:accounts_customuser_changelist'))
        self.assertEqual(response.status_code, 200)
        
        # Test product management
        response = self.client.get(reverse('admin:products_product_changelist'))
        self.assertEqual(response.status_code, 200)
        
        # Test category management
        response = self.client.get(reverse('admin:products_category_changelist'))
        self.assertEqual(response.status_code, 200)
        
        # Test booking management
        response = self.client.get(reverse('admin:products_booking_changelist'))
        self.assertEqual(response.status_code, 200)

    def test_admin_permissions_work_correctly(self):
        """Test that admin permissions work correctly across apps"""
        # Regular user cannot access admin
        self.client.login(email='regular@example.com', password='regularpass123')
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 403)  # Forbidden
        
        # Admin can access admin
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_view_user_bookings(self):
        """Test that admin can view and manage user bookings"""
        # Create booking
        booking = Booking.objects.create(
            product=self.product,
            user=self.regular_user,
            session_date=date(2024, 1, 15),
            session_time=time(14, 0),
            notes='Test booking'
        )
        
        # Admin can view booking
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('admin:products_booking_change', args=[booking.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test booking') 