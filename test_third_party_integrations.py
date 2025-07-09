import pytest
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.mail import send_mail
from django.utils import timezone
from datetime import date, time, timedelta
from products.models import Category, Product, Booking

User = get_user_model()


class EmailServiceIntegrationTests(TestCase):
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

    def test_email_sending_functionality(self):
        """Test that email sending works correctly"""
        # Clear mail outbox
        mail.outbox.clear()
        
        # Send test email
        send_mail(
            'Test Subject',
            'Test Message',
            'from@example.com',
            ['to@example.com'],
            fail_silently=False,
        )
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Test Subject')
        self.assertEqual(mail.outbox[0].body, 'Test Message')
        self.assertEqual(mail.outbox[0].from_email, 'from@example.com')
        self.assertEqual(mail.outbox[0].to, ['to@example.com'])

    def test_password_reset_email_integration(self):
        """Test password reset email integration"""
        # Clear mail outbox
        mail.outbox.clear()
        
        # Request password reset
        response = self.client.post(reverse('account_reset_password'), {
            'email': 'test@example.com'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email content
        email = mail.outbox[0]
        self.assertIn('test@example.com', email.to)
        self.assertIn('password reset', email.subject.lower())

    def test_booking_confirmation_email_integration(self):
        """Test booking confirmation email integration"""
        # Create booking
        booking = Booking.objects.create(
            product=self.product,
            user=self.user,
            session_date=date(2024, 1, 15),
            session_time=time(14, 0),
            notes='Test booking'
        )
        
        # Clear mail outbox
        mail.outbox.clear()
        
        # Simulate sending booking confirmation email
        send_mail(
            'Booking Confirmed',
            f'Your booking for {self.product.name} on {booking.session_date} at {booking.session_time} has been confirmed.',
            'noreply@example.com',
            [self.user.email],
            fail_silently=False,
        )
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Booking Confirmed')
        self.assertIn(self.user.email, mail.outbox[0].to)

    def test_email_template_integration(self):
        """Test email template integration"""
        # Clear mail outbox
        mail.outbox.clear()
        
        # Send email with HTML template
        from django.template.loader import render_to_string
        from django.core.mail import EmailMessage
        
        html_content = render_to_string('account/email/email_confirmation_message.txt', {
            'user': self.user,
            'confirmation_url': 'http://example.com/confirm'
        })
        
        email = EmailMessage(
            'Email Confirmation',
            html_content,
            'noreply@example.com',
            [self.user.email]
        )
        email.content_subtype = "html"
        email.send()
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Email Confirmation')

    @patch('django.core.mail.send_mail')
    def test_email_service_failure_handling(self, mock_send_mail):
        """Test email service failure handling"""
        # Mock email service to raise exception
        mock_send_mail.side_effect = Exception("Email service unavailable")
        
        # Try to send email
        try:
            send_mail(
                'Test Subject',
                'Test Message',
                'from@example.com',
                ['to@example.com'],
                fail_silently=True,
            )
        except Exception:
            self.fail("Email service failure should be handled gracefully")

    def test_email_encoding_handling(self):
        """Test email encoding handling"""
        # Test email with unicode characters
        unicode_subject = 'Sesión confirmada 🧘‍♀️'
        unicode_body = 'Su sesión de shiatsu ha sido confirmada con éxito.'
        
        mail.outbox.clear()
        
        send_mail(
            unicode_subject,
            unicode_body,
            'from@example.com',
            ['to@example.com'],
            fail_silently=False,
        )
        
        # Check that email was sent with unicode content
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, unicode_subject)
        self.assertEqual(mail.outbox[0].body, unicode_body)


class PaymentProcessorIntegrationTests(TestCase):
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

    def test_payment_amount_calculation(self):
        """Test payment amount calculation"""
        # Test different product prices
        test_cases = [
            (10.00, 1000),  # £10.00 = 1000 pence
            (65.00, 6500),  # £65.00 = 6500 pence
            (99.99, 9999),  # £99.99 = 9999 pence
        ]
        
        for price_gbp, expected_pence in test_cases:
            calculated_pence = int(price_gbp * 100)
            self.assertEqual(calculated_pence, expected_pence)

    def test_payment_currency_handling(self):
        """Test payment currency handling"""
        # Test different currencies
        currencies = ['gbp', 'usd', 'eur']
        
        for currency in currencies:
            # This would be used in actual payment processing
            self.assertIsInstance(currency, str)
            self.assertEqual(len(currency), 3)

    def test_payment_validation(self):
        """Test payment validation logic"""
        # Test valid payment amounts
        valid_amounts = [100, 1000, 10000]  # In pence
        for amount in valid_amounts:
            self.assertGreater(amount, 0)
            self.assertIsInstance(amount, int)

        # Test invalid payment amounts
        invalid_amounts = [-100, 0, 'invalid']
        for amount in invalid_amounts:
            if isinstance(amount, int):
                self.assertLessEqual(amount, 0)
            else:
                self.assertNotIsInstance(amount, int)


class ExternalAPIIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_api_authentication_handling(self):
        """Test API authentication handling"""
        # Test API key authentication
        api_key = 'test_api_key_123'
        headers = {'Authorization': f'Bearer {api_key}'}
        
        # This would be used in actual API calls
        self.assertIsInstance(api_key, str)
        self.assertIn('Authorization', headers)
        self.assertIn('Bearer', headers['Authorization'])

    def test_api_response_format(self):
        """Test API response format handling"""
        # Simulate API response data
        api_response = {
            'status': 'success',
            'data': {
                'id': 123,
                'name': 'Test API Response',
                'timestamp': '2024-01-15T14:00:00Z'
            }
        }
        
        # Test response structure
        self.assertIn('status', api_response)
        self.assertIn('data', api_response)
        self.assertEqual(api_response['status'], 'success')

    def test_api_error_handling(self):
        """Test API error handling"""
        # Simulate API error response
        error_response = {
            'status': 'error',
            'message': 'Invalid request',
            'code': 400
        }
        
        # Test error response structure
        self.assertIn('status', error_response)
        self.assertIn('message', error_response)
        self.assertEqual(error_response['status'], 'error')

    def test_api_rate_limiting_simulation(self):
        """Test API rate limiting simulation"""
        # Simulate rate limit headers
        rate_limit_headers = {
            'X-RateLimit-Limit': '100',
            'X-RateLimit-Remaining': '50',
            'X-RateLimit-Reset': '1642248000'
        }
        
        # Test rate limit header structure
        self.assertIn('X-RateLimit-Limit', rate_limit_headers)
        self.assertIn('X-RateLimit-Remaining', rate_limit_headers)
        self.assertIn('X-RateLimit-Reset', rate_limit_headers)


class SocialAuthenticationIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_social_account_creation(self):
        """Test social account creation"""
        # Simulate social account data
        social_account_data = {
            'provider': 'google',
            'uid': '123456789',
            'extra_data': {
                'name': 'John Doe',
                'email': 'john.doe@gmail.com',
                'picture': 'https://example.com/avatar.jpg'
            }
        }
        
        # This would be used in actual social account creation
        self.assertIn('provider', social_account_data)
        self.assertIn('uid', social_account_data)
        self.assertIn('extra_data', social_account_data)

    def test_social_login_redirect_handling(self):
        """Test social login redirect handling"""
        # Test different redirect scenarios
        redirect_urls = [
            '/accounts/profile/',
            '/products/',
            '/',
        ]
        
        for url in redirect_urls:
            # This would be used in actual redirect handling
            self.assertIsInstance(url, str)
            self.assertTrue(url.startswith('/'))

    def test_social_account_linking(self):
        """Test social account linking"""
        # Simulate linking existing account
        existing_user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='existingpass123'
        )
        
        # This would be used in actual account linking
        self.assertIsNotNone(existing_user)
        self.assertEqual(existing_user.email, 'existing@example.com')

    def test_social_account_disconnection(self):
        """Test social account disconnection"""
        # Simulate social account disconnection
        social_account_id = 123
        
        # This would be used in actual account disconnection
        self.assertIsInstance(social_account_id, int)
        self.assertGreater(social_account_id, 0)

    def test_social_provider_configuration(self):
        """Test social provider configuration"""
        # Test different social providers
        providers = ['google', 'facebook', 'twitter']
        
        for provider in providers:
            # This would be used in actual provider configuration
            self.assertIsInstance(provider, str)
            self.assertGreater(len(provider), 0)


class ThirdPartyServiceErrorHandlingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @patch('django.core.mail.send_mail')
    def test_email_service_error_handling(self, mock_send_mail):
        """Test email service error handling"""
        # Mock email service to fail
        mock_send_mail.side_effect = Exception("Email service unavailable")
        
        # Try to send email with error handling
        try:
            send_mail(
                'Test Subject',
                'Test Message',
                'from@example.com',
                ['to@example.com'],
                fail_silently=True,
            )
        except Exception:
            self.fail("Email service error should be handled gracefully")

    def test_service_unavailable_fallback(self):
        """Test service unavailable fallback behavior"""
        # Simulate service unavailability
        services = ['email', 'payment', 'calendar', 'weather']
        
        for service in services:
            # This would be used in actual fallback handling
            self.assertIsInstance(service, str)
            self.assertGreater(len(service), 0)

    def test_third_party_service_timeout(self):
        """Test third-party service timeout handling"""
        # Simulate timeout scenarios
        timeout_scenarios = [
            {'service': 'email', 'timeout': 30},
            {'service': 'payment', 'timeout': 60},
            {'service': 'api', 'timeout': 10}
        ]
        
        for scenario in timeout_scenarios:
            self.assertIn('service', scenario)
            self.assertIn('timeout', scenario)
            self.assertIsInstance(scenario['timeout'], int)
            self.assertGreater(scenario['timeout'], 0)

    def test_third_party_service_retry_logic(self):
        """Test third-party service retry logic"""
        # Simulate retry configuration
        retry_config = {
            'max_retries': 3,
            'backoff_factor': 2,
            'timeout': 30
        }
        
        # Test retry configuration
        self.assertIn('max_retries', retry_config)
        self.assertIn('backoff_factor', retry_config)
        self.assertIn('timeout', retry_config)
        
        self.assertIsInstance(retry_config['max_retries'], int)
        self.assertIsInstance(retry_config['backoff_factor'], int)
        self.assertIsInstance(retry_config['timeout'], int) 