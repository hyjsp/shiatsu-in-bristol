import pytest
from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from products.models import Category, Product, Booking
from products.views import product_list, product_detail, booking_confirmation

User = get_user_model()


class ProductURLTests(TestCase):
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

    def test_product_list_url(self):
        """Test that product list URL resolves correctly"""
        url = reverse('products:product_list')
        self.assertEqual(url, '/products/')
        
        # Test URL resolution
        resolver = resolve(url)
        self.assertEqual(resolver.func, product_list)

    def test_product_detail_url(self):
        """Test that product detail URL resolves correctly"""
        url = reverse('products:product_detail', args=[self.product.pk])
        self.assertEqual(url, f'/products/{self.product.pk}/')
        
        # Test URL resolution
        resolver = resolve(url)
        self.assertEqual(resolver.func, product_detail)

    def test_booking_confirmation_url(self):
        """Test that booking confirmation URL resolves correctly"""
        booking = Booking.objects.create(
            product=self.product,
            user=self.user,
            session_date='2024-01-15',
            session_time='14:00',
            notes='Test booking'
        )
        url = reverse('products:booking_confirmation', args=[booking.pk])
        self.assertEqual(url, f'/products/booking/confirmation/{booking.pk}/')
        
        # Test URL resolution
        resolver = resolve(url)
        self.assertEqual(resolver.func, booking_confirmation)

    def test_url_namespacing(self):
        """Test that URLs are properly namespaced"""
        # Test that URLs include the 'products' namespace
        product_list_url = reverse('products:product_list')
        self.assertIn('/products/', product_list_url)
        
        product_detail_url = reverse('products:product_detail', args=[self.product.pk])
        self.assertIn('/products/', product_detail_url)

    def test_url_parameter_handling(self):
        """Test that URL parameters are handled correctly"""
        # Test with valid product ID
        url = reverse('products:product_detail', args=[self.product.pk])
        resolver = resolve(url)
        self.assertEqual(resolver.kwargs['pk'], self.product.pk)
        
        # Test booking confirmation with valid booking ID
        booking = Booking.objects.create(
            product=self.product,
            user=self.user,
            session_date='2024-01-15',
            session_time='14:00',
            notes='Test booking'
        )
        url = reverse('products:booking_confirmation', args=[booking.pk])
        resolver = resolve(url)
        self.assertEqual(resolver.kwargs['pk'], booking.pk)

    def test_url_patterns_exist(self):
        """Test that all expected URL patterns exist"""
        # Test product list URL exists
        try:
            reverse('products:product_list')
        except:
            self.fail("Product list URL does not exist")
        
        # Test product detail URL exists
        try:
            reverse('products:product_detail', args=[self.product.pk])
        except:
            self.fail("Product detail URL does not exist")
        
        # Test booking confirmation URL exists
        booking = Booking.objects.create(
            product=self.product,
            user=self.user,
            session_date='2024-01-15',
            session_time='14:00',
            notes='Test booking'
        )
        try:
            reverse('products:booking_confirmation', args=[booking.pk])
        except:
            self.fail("Booking confirmation URL does not exist")

    def test_url_404_handling(self):
        """Test that invalid URLs return 404"""
        # Test invalid product ID
        response = self.client.get('/products/99999/')
        self.assertEqual(response.status_code, 302)  # Redirect to login for @login_required
        
        # Test invalid booking ID
        response = self.client.get('/products/booking/confirmation/99999/')
        self.assertEqual(response.status_code, 302)  # Redirect to login for @login_required

    def test_url_trailing_slash_handling(self):
        """Test that URLs handle trailing slashes correctly"""
        # Test product list with and without trailing slash
        url_with_slash = reverse('products:product_list')
        self.assertTrue(url_with_slash.endswith('/'))
        
        # Test product detail with trailing slash
        url_with_slash = reverse('products:product_detail', args=[self.product.pk])
        self.assertTrue(url_with_slash.endswith('/'))

    def test_url_case_sensitivity(self):
        """Test that URLs are case sensitive as expected"""
        # Test that URL patterns are case sensitive
        response = self.client.get('/Products/')  # Wrong case
        self.assertEqual(response.status_code, 404)
        
        response = self.client.get('/products/')  # Correct case
        self.assertEqual(response.status_code, 200)

    def test_url_parameter_types(self):
        """Test that URL parameters are of correct types"""
        # Test that product ID is integer
        url = reverse('products:product_detail', args=[self.product.pk])
        resolver = resolve(url)
        self.assertIsInstance(resolver.kwargs['pk'], int)
        
        # Test that booking ID is integer
        booking = Booking.objects.create(
            product=self.product,
            user=self.user,
            session_date='2024-01-15',
            session_time='14:00',
            notes='Test booking'
        )
        url = reverse('products:booking_confirmation', args=[booking.pk])
        resolver = resolve(url)
        self.assertIsInstance(resolver.kwargs['pk'], int)

    def test_url_reverse_with_kwargs(self):
        """Test that URL reverse works with kwargs"""
        # Test product detail with kwargs
        url = reverse('products:product_detail', kwargs={'pk': self.product.pk})
        self.assertEqual(url, f'/products/{self.product.pk}/')
        
        # Test booking confirmation with kwargs
        booking = Booking.objects.create(
            product=self.product,
            user=self.user,
            session_date='2024-01-15',
            session_time='14:00',
            notes='Test booking'
        )
        url = reverse('products:booking_confirmation', kwargs={'pk': booking.pk})
        self.assertEqual(url, f'/products/booking/confirmation/{booking.pk}/') 