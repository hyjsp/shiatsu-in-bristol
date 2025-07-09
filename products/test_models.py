import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import date, time, timedelta
from django.contrib.auth import get_user_model
from products.models import Category, Product, Booking

User = get_user_model()


class CategoryModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Shiatsu Sessions',
            description='Relaxing shiatsu massage sessions'
        )

    def test_category_str_method(self):
        """Test that Category string representation works correctly"""
        self.assertEqual(str(self.category), 'Shiatsu Sessions')

    def test_category_creation(self):
        """Test that Category can be created with required fields"""
        self.assertEqual(self.category.name, 'Shiatsu Sessions')
        self.assertEqual(self.category.description, 'Relaxing shiatsu massage sessions')

    def test_category_blank_description(self):
        """Test that Category can be created without description"""
        category = Category.objects.create(name='Test Category')
        self.assertEqual(category.description, '')


class ProductModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Shiatsu Sessions')
        self.product = Product.objects.create(
            category=self.category,
            name='60-Minute Session',
            description='A relaxing 60-minute session',
            price=65.00,
            duration_minutes=60,
            is_active=True
        )

    def test_product_str_method(self):
        """Test that Product string representation works correctly"""
        self.assertEqual(str(self.product), '60-Minute Session')

    def test_product_creation(self):
        """Test that Product can be created with all fields"""
        self.assertEqual(self.product.name, '60-Minute Session')
        self.assertEqual(self.product.category, self.category)
        self.assertEqual(self.product.price, 65.00)
        self.assertEqual(self.product.duration_minutes, 60)
        self.assertTrue(self.product.is_active)

    def test_product_related_name(self):
        """Test that related name works for category.products"""
        products = self.category.products.all()
        self.assertIn(self.product, products)

    def test_product_inactive_default(self):
        """Test that new products are active by default"""
        product = Product.objects.create(
            category=self.category,
            name='Test Product',
            price=50.00
        )
        self.assertTrue(product.is_active)

    def test_product_optional_duration(self):
        """Test that duration_minutes can be null/blank"""
        product = Product.objects.create(
            category=self.category,
            name='Test Product',
            price=50.00,
            duration_minutes=None
        )
        self.assertIsNone(product.duration_minutes)

    def test_product_price_decimal_places(self):
        """Test that price handles decimal places correctly"""
        product = Product.objects.create(
            category=self.category,
            name='Test Product',
            price=45.50
        )
        self.assertEqual(product.price, 45.50)


class BookingModelTests(TestCase):
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
            notes='Test booking'
        )

    def test_booking_str_method(self):
        """Test that Booking string representation works correctly"""
        expected = f"{self.user} - {self.product} on 2024-01-15 at 14:00:00"
        self.assertEqual(str(self.booking), expected)

    def test_booking_creation(self):
        """Test that Booking can be created with all fields"""
        self.assertEqual(self.booking.product, self.product)
        self.assertEqual(self.booking.user, self.user)
        self.assertEqual(self.booking.session_date, date(2024, 1, 15))
        self.assertEqual(self.booking.session_time, time(14, 0))
        self.assertEqual(self.booking.notes, 'Test booking')

    def test_booking_related_name(self):
        """Test that related names work for user.bookings and product.bookings"""
        user_bookings = self.user.bookings.all()
        product_bookings = self.product.bookings.all()
        
        self.assertIn(self.booking, user_bookings)
        self.assertIn(self.booking, product_bookings)

    def test_booking_auto_created_at(self):
        """Test that created_at is automatically set"""
        self.assertIsNotNone(self.booking.created_at)
        self.assertIsInstance(self.booking.created_at, timezone.datetime)

    def test_booking_blank_notes(self):
        """Test that notes can be blank"""
        booking = Booking.objects.create(
            product=self.product,
            user=self.user,
            session_date=date(2024, 1, 16),
            session_time=time(15, 0)
        )
        self.assertEqual(booking.notes, '')

    def test_booking_cascade_delete_product(self):
        """Test that bookings are deleted when product is deleted"""
        booking_id = self.booking.id
        self.product.delete()
        self.assertFalse(Booking.objects.filter(id=booking_id).exists())

    def test_booking_cascade_delete_user(self):
        """Test that bookings are deleted when user is deleted"""
        booking_id = self.booking.id
        self.user.delete()
        self.assertFalse(Booking.objects.filter(id=booking_id).exists())


class ModelRelationshipTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Shiatsu Sessions')
        self.product1 = Product.objects.create(
            category=self.category,
            name='60-Minute Session',
            price=65.00,
            duration_minutes=60,
            is_active=True
        )
        self.product2 = Product.objects.create(
            category=self.category,
            name='90-Minute Session',
            price=85.00,
            duration_minutes=90,
            is_active=True
        )

    def test_category_products_relationship(self):
        """Test that category.products returns all products in category"""
        products = self.category.products.all()
        self.assertEqual(products.count(), 2)
        self.assertIn(self.product1, products)
        self.assertIn(self.product2, products)

    def test_user_bookings_relationship(self):
        """Test that user.bookings returns all bookings for user"""
        booking1 = Booking.objects.create(
            product=self.product1,
            user=self.user,
            session_date=date(2024, 1, 15),
            session_time=time(14, 0)
        )
        booking2 = Booking.objects.create(
            product=self.product2,
            user=self.user,
            session_date=date(2024, 1, 16),
            session_time=time(15, 0)
        )
        
        user_bookings = self.user.bookings.all()
        self.assertEqual(user_bookings.count(), 2)
        self.assertIn(booking1, user_bookings)
        self.assertIn(booking2, user_bookings)

    def test_product_bookings_relationship(self):
        """Test that product.bookings returns all bookings for product"""
        booking1 = Booking.objects.create(
            product=self.product1,
            user=self.user,
            session_date=date(2024, 1, 15),
            session_time=time(14, 0)
        )
        booking2 = Booking.objects.create(
            product=self.product1,
            user=self.user,
            session_date=date(2024, 1, 16),
            session_time=time(15, 0)
        )
        
        product_bookings = self.product1.bookings.all()
        self.assertEqual(product_bookings.count(), 2)
        self.assertIn(booking1, product_bookings)
        self.assertIn(booking2, product_bookings) 