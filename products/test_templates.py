import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from datetime import date, time, timedelta
from products.models import Category, Product, Booking
from products.views import product_list, product_detail, booking_confirmation

User = get_user_model()


class ProductListTemplateTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
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

    def test_product_list_template_context(self):
        """Test that product list template receives correct context"""
        request = self.factory.get(reverse('products:product_list'))
        response = product_list(request)
        
        # Check that products are in context
        self.assertIn('products', response.context_data)
        products = response.context_data['products']
        self.assertEqual(products.count(), 1)
        self.assertEqual(products.first(), self.product)

    def test_product_list_template_rendering(self):
        """Test that product list template renders correctly"""
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        
        # Check for expected content
        self.assertContains(response, '60-Minute Session')
        self.assertContains(response, '£65.00')
        self.assertContains(response, 'Book a Shiatsu Session')

    def test_product_list_template_with_no_products(self):
        """Test product list template with no active products"""
        # Deactivate the product
        self.product.is_active = False
        self.product.save()
        
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        
        # Should not contain the inactive product
        self.assertNotContains(response, '60-Minute Session')

    def test_product_list_template_with_multiple_products(self):
        """Test product list template with multiple products"""
        # Create additional products
        Product.objects.create(
            category=self.category,
            name='30-Minute Session',
            description='A quick 30-minute session',
            price=35.00,
            duration_minutes=30,
            is_active=True
        )
        Product.objects.create(
            category=self.category,
            name='90-Minute Session',
            description='An extended 90-minute session',
            price=95.00,
            duration_minutes=90,
            is_active=True
        )
        
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        
        # Check for all products
        self.assertContains(response, '30-Minute Session')
        self.assertContains(response, '60-Minute Session')
        self.assertContains(response, '90-Minute Session')

    def test_product_list_template_inheritance(self):
        """Test that product list template inherits from base template"""
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        
        # Check for base template elements
        self.assertContains(response, '<html')
        self.assertContains(response, '<head')
        self.assertContains(response, '<body')


class ProductDetailTemplateTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
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

    def test_product_detail_template_context(self):
        """Test that product detail template receives correct context"""
        self.client.login(email='test@example.com', password='testpass123')
        request = self.factory.get(reverse('products:product_detail', args=[self.product.pk]))
        request.user = self.user
        response = product_detail(request, pk=self.product.pk)
        
        # Check that product and form are in context
        self.assertIn('product', response.context_data)
        self.assertIn('form', response.context_data)
        self.assertEqual(response.context_data['product'], self.product)

    def test_product_detail_template_rendering(self):
        """Test that product detail template renders correctly"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Check for expected content
        self.assertContains(response, '60-Minute Session')
        self.assertContains(response, '£65.00')
        self.assertContains(response, 'Book this session')

    def test_product_detail_template_form_rendering(self):
        """Test that booking form renders correctly in template"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Check for form elements
        self.assertContains(response, 'type="date"')
        self.assertContains(response, 'type="time"')
        self.assertContains(response, 'form-control')

    def test_product_detail_template_inactive_product(self):
        """Test product detail template with inactive product"""
        self.product.is_active = False
        self.product.save()
        
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 404)

    def test_product_detail_template_inheritance(self):
        """Test that product detail template inherits from base template"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Check for base template elements
        self.assertContains(response, '<html')
        self.assertContains(response, '<head')
        self.assertContains(response, '<body')


class BookingConfirmationTemplateTests(TestCase):
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
        self.booking = Booking.objects.create(
            product=self.product,
            user=self.user,
            session_date=date(2024, 1, 15),
            session_time=time(14, 0),
            notes='Test booking notes'
        )

    def test_booking_confirmation_template_context(self):
        """Test that booking confirmation template receives correct context"""
        self.client.login(email='test@example.com', password='testpass123')
        request = self.factory.get(reverse('products:booking_confirmation', args=[self.booking.pk]))
        request.user = self.user
        response = booking_confirmation(request, pk=self.booking.pk)
        
        # Check that booking is in context
        self.assertIn('booking', response.context_data)
        self.assertEqual(response.context_data['booking'], self.booking)

    def test_booking_confirmation_template_rendering(self):
        """Test that booking confirmation template renders correctly"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('products:booking_confirmation', args=[self.booking.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Check for expected content
        self.assertContains(response, 'Booking Confirmed!')
        self.assertContains(response, '60-Minute Session')
        self.assertContains(response, 'Jan. 15, 2024')
        self.assertContains(response, '2 p.m.')
        self.assertContains(response, 'Test booking notes')

    def test_booking_confirmation_template_wrong_user(self):
        """Test booking confirmation template with wrong user"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        self.client.login(email='other@example.com', password='testpass123')
        response = self.client.get(reverse('products:booking_confirmation', args=[self.booking.pk]))
        self.assertEqual(response.status_code, 404)

    def test_booking_confirmation_template_inheritance(self):
        """Test that booking confirmation template inherits from base template"""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('products:booking_confirmation', args=[self.booking.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Check for base template elements
        self.assertContains(response, '<html')
        self.assertContains(response, '<head')
        self.assertContains(response, '<body')


class TemplateRenderingTests(TestCase):
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
            description='A relaxing 60-minute session',
            price=65.00,
            duration_minutes=60,
            is_active=True
        )

    def test_template_rendering_with_empty_data(self):
        """Test template rendering with empty product list"""
        Product.objects.all().delete()
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        # Should still render without errors

    def test_template_rendering_with_large_data(self):
        """Test template rendering with many products"""
        # Create many products
        for i in range(20):
            Product.objects.create(
                category=self.category,
                name=f'Session {i}',
                description=f'Description {i}',
                price=50.00 + i,
                duration_minutes=60,
                is_active=True
            )
        
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        # Should render without performance issues

    def test_template_rendering_with_special_characters(self):
        """Test template rendering with special characters in data"""
        product = Product.objects.create(
            category=self.category,
            name='Session with "quotes" & <tags>',
            description='Description with "quotes" & <tags>',
            price=65.00,
            duration_minutes=60,
            is_active=True
        )
        
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        # Should handle special characters properly

    def test_template_rendering_with_unicode_data(self):
        """Test template rendering with unicode characters"""
        product = Product.objects.create(
            category=self.category,
            name='Sesión con acentos',
            description='Descripción con ñ y áéíóú',
            price=65.00,
            duration_minutes=60,
            is_active=True
        )
        
        response = self.client.get(reverse('products:product_list'))
        self.assertEqual(response.status_code, 200)
        # Should handle unicode characters properly 