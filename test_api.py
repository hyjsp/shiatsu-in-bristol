import pytest
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, time, timedelta
from products.models import Category, Product, Booking
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class ProductAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
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

    def test_product_list_api(self):
        """Test GET /api/products/ endpoint"""
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('results', response.data)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        
        # Check that products are included
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], '60-Minute Session')

    def test_product_detail_api(self):
        """Test GET /api/products/{id}/ endpoint"""
        response = self.client.get(f'/api/products/{self.product.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertEqual(response.data['name'], '60-Minute Session')
        self.assertEqual(response.data['price'], '65.00')
        self.assertEqual(response.data['duration_minutes'], 60)
        self.assertTrue(response.data['is_active'])

    def test_product_create_api(self):
        """Test POST /api/products/ endpoint"""
        self.client.force_authenticate(user=self.user)
        
        product_data = {
            'category': self.category.pk,
            'name': '90-Minute Session',
            'description': 'An extended 90-minute session',
            'price': '95.00',
            'duration_minutes': 90,
            'is_active': True
        }
        
        response = self.client.post('/api/products/', product_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that product was created
        self.assertEqual(Product.objects.count(), 2)
        new_product = Product.objects.get(name='90-Minute Session')
        self.assertEqual(new_product.price, 95.00)

    def test_product_update_api(self):
        """Test PUT /api/products/{id}/ endpoint"""
        self.client.force_authenticate(user=self.user)
        
        update_data = {
            'category': self.category.pk,
            'name': 'Updated 60-Minute Session',
            'description': 'An updated 60-minute session',
            'price': '70.00',
            'duration_minutes': 60,
            'is_active': True
        }
        
        response = self.client.put(f'/api/products/{self.product.pk}/', update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that product was updated
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Updated 60-Minute Session')
        self.assertEqual(self.product.price, 70.00)

    def test_product_delete_api(self):
        """Test DELETE /api/products/{id}/ endpoint"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.delete(f'/api/products/{self.product.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Check that product was deleted
        self.assertEqual(Product.objects.count(), 0)

    def test_product_api_authentication_required(self):
        """Test that API endpoints require authentication for write operations"""
        # Try to create product without authentication
        product_data = {
            'category': self.category.pk,
            'name': 'Unauthorized Session',
            'price': '50.00',
            'duration_minutes': 60,
            'is_active': True
        }
        
        response = self.client.post('/api/products/', product_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_product_api_pagination(self):
        """Test API pagination"""
        # Create multiple products
        for i in range(25):
            Product.objects.create(
                category=self.category,
                name=f'Paginated Session {i}',
                description=f'Description {i}',
                price=50.00 + i,
                duration_minutes=60,
                is_active=True
            )
        
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check pagination
        self.assertEqual(len(response.data['results']), 20)  # Default page size
        self.assertEqual(response.data['count'], 26)  # 25 new + 1 original
        self.assertIsNotNone(response.data['next'])

    def test_product_api_filtering(self):
        """Test API filtering capabilities"""
        # Create products with different prices
        Product.objects.create(
            category=self.category,
            name='Cheap Session',
            price=30.00,
            duration_minutes=30,
            is_active=True
        )
        Product.objects.create(
            category=self.category,
            name='Expensive Session',
            price=100.00,
            duration_minutes=90,
            is_active=True
        )
        
        # Filter by price range
        response = self.client.get('/api/products/?min_price=50&max_price=80')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only return products in price range
        for product in response.data['results']:
            price = float(product['price'])
            self.assertGreaterEqual(price, 50.0)
            self.assertLessEqual(price, 80.0)

    def test_product_api_search(self):
        """Test API search functionality"""
        # Create products with searchable names
        Product.objects.create(
            category=self.category,
            name='Relaxing Session',
            price=65.00,
            duration_minutes=60,
            is_active=True
        )
        Product.objects.create(
            category=self.category,
            name='Therapeutic Session',
            price=75.00,
            duration_minutes=60,
            is_active=True
        )
        
        # Search for 'Relaxing'
        response = self.client.get('/api/products/?search=Relaxing')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should return only products with 'Relaxing' in name
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Relaxing Session')


class BookingAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
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
            notes='Test booking'
        )

    def test_booking_list_api(self):
        """Test GET /api/bookings/ endpoint"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/bookings/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['notes'], 'Test booking')

    def test_booking_detail_api(self):
        """Test GET /api/bookings/{id}/ endpoint"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(f'/api/bookings/{self.booking.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertEqual(response.data['notes'], 'Test booking')
        self.assertEqual(response.data['session_date'], '2024-01-15')
        self.assertEqual(response.data['session_time'], '14:00:00')

    def test_booking_create_api(self):
        """Test POST /api/bookings/ endpoint"""
        self.client.force_authenticate(user=self.user)
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        booking_data = {
            'product': self.product.pk,
            'session_date': tomorrow,
            'session_time': '15:00',
            'notes': 'API created booking'
        }
        
        response = self.client.post('/api/bookings/', booking_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that booking was created
        self.assertEqual(Booking.objects.count(), 2)
        new_booking = Booking.objects.get(notes='API created booking')
        self.assertEqual(new_booking.user, self.user)

    def test_booking_update_api(self):
        """Test PUT /api/bookings/{id}/ endpoint"""
        self.client.force_authenticate(user=self.user)
        
        tomorrow = timezone.now().date() + timedelta(days=1)
        update_data = {
            'product': self.product.pk,
            'session_date': tomorrow,
            'session_time': '16:00',
            'notes': 'Updated booking notes'
        }
        
        response = self.client.put(f'/api/bookings/{self.booking.pk}/', update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that booking was updated
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.notes, 'Updated booking notes')
        self.assertEqual(self.booking.session_time, time(16, 0))

    def test_booking_delete_api(self):
        """Test DELETE /api/bookings/{id}/ endpoint"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.delete(f'/api/bookings/{self.booking.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Check that booking was deleted
        self.assertEqual(Booking.objects.count(), 0)

    def test_booking_api_user_isolation(self):
        """Test that users can only access their own bookings"""
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
        
        self.client.force_authenticate(user=self.user)
        
        # Try to access other user's booking
        response = self.client.get(f'/api/bookings/{other_booking.pk}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_booking_api_validation(self):
        """Test API validation for booking creation"""
        self.client.force_authenticate(user=self.user)
        
        # Try to create booking with past date
        yesterday = timezone.now().date() - timedelta(days=1)
        invalid_data = {
            'product': self.product.pk,
            'session_date': yesterday,
            'session_time': '14:00',
            'notes': 'Invalid booking'
        }
        
        response = self.client.post('/api/bookings/', invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check error message
        self.assertIn('session_date', response.data)


class CategoryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Shiatsu Sessions')

    def test_category_list_api(self):
        """Test GET /api/categories/ endpoint"""
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Shiatsu Sessions')

    def test_category_detail_api(self):
        """Test GET /api/categories/{id}/ endpoint"""
        response = self.client.get(f'/api/categories/{self.category.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response structure
        self.assertEqual(response.data['name'], 'Shiatsu Sessions')

    def test_category_create_api(self):
        """Test POST /api/categories/ endpoint"""
        self.client.force_authenticate(user=self.user)
        
        category_data = {
            'name': 'Massage Therapy',
            'description': 'Various massage therapy sessions'
        }
        
        response = self.client.post('/api/categories/', category_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that category was created
        self.assertEqual(Category.objects.count(), 2)
        new_category = Category.objects.get(name='Massage Therapy')
        self.assertEqual(new_category.description, 'Various massage therapy sessions')


class APIErrorHandlingTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_api_404_error(self):
        """Test API 404 error handling"""
        response = self.client.get('/api/products/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Check error response structure
        self.assertIn('detail', response.data)

    def test_api_400_error(self):
        """Test API 400 error handling"""
        self.client.force_authenticate(user=self.user)
        
        # Try to create product with invalid data
        invalid_data = {
            'name': '',  # Empty name
            'price': 'invalid_price'  # Invalid price
        }
        
        response = self.client.post('/api/products/', invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check error response structure
        self.assertIn('name', response.data)
        self.assertIn('price', response.data)

    def test_api_401_error(self):
        """Test API 401 error handling"""
        # Try to access protected endpoint without authentication
        response = self.client.post('/api/products/', {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_api_403_error(self):
        """Test API 403 error handling"""
        # Create regular user (not admin)
        regular_user = User.objects.create_user(
            username='regularuser',
            email='regular@example.com',
            password='regularpass123'
        )
        
        self.client.force_authenticate(user=regular_user)
        
        # Try to access admin-only endpoint
        response = self.client.delete('/api/products/1/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_api_500_error_handling(self):
        """Test API 500 error handling"""
        # This test would require a view that intentionally raises an exception
        # For now, we'll test that normal API calls don't result in 500 errors
        
        response = self.client.get('/api/products/')
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class APIResponseFormatTests(TestCase):
    def setUp(self):
        self.client = APIClient()
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

    def test_api_json_response_format(self):
        """Test that API responses are properly formatted JSON"""
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check content type
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Check that response is valid JSON
        try:
            json.loads(response.content)
        except json.JSONDecodeError:
            self.fail("Response is not valid JSON")

    def test_api_response_structure(self):
        """Test that API responses have consistent structure"""
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check pagination structure
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        
        # Check that count is an integer
        self.assertIsInstance(response.data['count'], int)
        
        # Check that results is a list
        self.assertIsInstance(response.data['results'], list)

    def test_api_detail_response_structure(self):
        """Test that API detail responses have consistent structure"""
        response = self.client.get(f'/api/products/{self.product.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check required fields
        self.assertIn('id', response.data)
        self.assertIn('name', response.data)
        self.assertIn('price', response.data)
        self.assertIn('duration_minutes', response.data)
        self.assertIn('is_active', response.data)
        
        # Check data types
        self.assertIsInstance(response.data['id'], int)
        self.assertIsInstance(response.data['name'], str)
        self.assertIsInstance(response.data['price'], str)
        self.assertIsInstance(response.data['duration_minutes'], int)
        self.assertIsInstance(response.data['is_active'], bool) 