import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import date, time
from products.models import Category, Product, Booking
from products.admin import CategoryAdmin, ProductAdmin, BookingAdmin

User = get_user_model()


class CategoryAdminTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.client = Client()
        self.client.login(email='admin@example.com', password='adminpass123')
        
        self.category = Category.objects.create(
            name='Shiatsu Sessions',
            description='Relaxing shiatsu massage sessions'
        )

    def test_category_admin_list_display(self):
        """Test that CategoryAdmin displays correct fields"""
        admin = CategoryAdmin(Category, None)
        expected_fields = ['name', 'description']
        self.assertEqual(admin.list_display, expected_fields)

    def test_category_admin_search_fields(self):
        """Test that CategoryAdmin has correct search fields"""
        admin = CategoryAdmin(Category, None)
        expected_fields = ['name']
        self.assertEqual(admin.search_fields, expected_fields)

    def test_category_admin_list_view(self):
        """Test that category admin list view loads correctly"""
        url = reverse('admin:products_category_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Shiatsu Sessions')

    def test_category_admin_detail_view(self):
        """Test that category admin detail view loads correctly"""
        url = reverse('admin:products_category_change', args=[self.category.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Shiatsu Sessions')

    def test_category_admin_add_view(self):
        """Test that category admin add view loads correctly"""
        url = reverse('admin:products_category_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_category_admin_search_functionality(self):
        """Test that category admin search works"""
        url = reverse('admin:products_category_changelist')
        response = self.client.get(url, {'q': 'Shiatsu'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Shiatsu Sessions')


class ProductAdminTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.client = Client()
        self.client.login(email='admin@example.com', password='adminpass123')
        
        self.category = Category.objects.create(name='Shiatsu Sessions')
        self.product = Product.objects.create(
            category=self.category,
            name='60-Minute Session',
            description='A relaxing 60-minute session',
            price=65.00,
            duration_minutes=60,
            is_active=True
        )

    def test_product_admin_list_display(self):
        """Test that ProductAdmin displays correct fields"""
        admin = ProductAdmin(Product, None)
        expected_fields = ['name', 'category', 'price', 'duration_minutes', 'is_active']
        self.assertEqual(admin.list_display, expected_fields)

    def test_product_admin_list_filter(self):
        """Test that ProductAdmin has correct filters"""
        admin = ProductAdmin(Product, None)
        expected_filters = ['category', 'is_active']
        self.assertEqual(admin.list_filter, expected_filters)

    def test_product_admin_search_fields(self):
        """Test that ProductAdmin has correct search fields"""
        admin = ProductAdmin(Product, None)
        expected_fields = ['name', 'description']
        self.assertEqual(admin.search_fields, expected_fields)

    def test_product_admin_list_view(self):
        """Test that product admin list view loads correctly"""
        url = reverse('admin:products_product_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '60-Minute Session')

    def test_product_admin_detail_view(self):
        """Test that product admin detail view loads correctly"""
        url = reverse('admin:products_product_change', args=[self.product.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '60-Minute Session')

    def test_product_admin_add_view(self):
        """Test that product admin add view loads correctly"""
        url = reverse('admin:products_product_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_product_admin_filter_functionality(self):
        """Test that product admin filters work"""
        url = reverse('admin:products_product_changelist')
        response = self.client.get(url, {'is_active__exact': '1'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '60-Minute Session')

    def test_product_admin_search_functionality(self):
        """Test that product admin search works"""
        url = reverse('admin:products_product_changelist')
        response = self.client.get(url, {'q': '60-Minute'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '60-Minute Session')

    def test_product_admin_category_filter(self):
        """Test that product admin category filter works"""
        url = reverse('admin:products_product_changelist')
        response = self.client.get(url, {'category__id__exact': self.category.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '60-Minute Session')


class BookingAdminTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.client = Client()
        self.client.login(email='admin@example.com', password='adminpass123')
        
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

    def test_booking_admin_list_display(self):
        """Test that BookingAdmin displays correct fields"""
        admin = BookingAdmin(Booking, None)
        expected_fields = ['user', 'product', 'session_date', 'session_time', 'created_at']
        self.assertEqual(admin.list_display, expected_fields)

    def test_booking_admin_list_filter(self):
        """Test that BookingAdmin has correct filters"""
        admin = BookingAdmin(Booking, None)
        expected_filters = ['session_date', 'product']
        self.assertEqual(admin.list_filter, expected_filters)

    def test_booking_admin_search_fields(self):
        """Test that BookingAdmin has correct search fields"""
        admin = BookingAdmin(Booking, None)
        expected_fields = ['user__email', 'product__name']
        self.assertEqual(admin.search_fields, expected_fields)

    def test_booking_admin_list_view(self):
        """Test that booking admin list view loads correctly"""
        url = reverse('admin:products_booking_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Check for booking content instead of email
        self.assertContains(response, '60-Minute Session')

    def test_booking_admin_detail_view(self):
        """Test that booking admin detail view loads correctly"""
        url = reverse('admin:products_booking_change', args=[self.booking.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '60-Minute Session')

    def test_booking_admin_add_view(self):
        """Test that booking admin add view loads correctly"""
        url = reverse('admin:products_booking_add')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_booking_admin_filter_functionality(self):
        """Test that booking admin filters work"""
        url = reverse('admin:products_booking_changelist')
        response = self.client.get(url, {'product__id__exact': self.product.pk})
        self.assertEqual(response.status_code, 200)

    def test_booking_admin_search_functionality(self):
        """Test that booking admin search works"""
        url = reverse('admin:products_booking_changelist')
        response = self.client.get(url, {'q': 'admin'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'admin')

    def test_booking_admin_date_filter(self):
        """Test that booking admin date filter works"""
        url = reverse('admin:products_booking_changelist')
        response = self.client.get(url, {'session_date__exact': '2024-01-15'})
        self.assertEqual(response.status_code, 200)


class AdminPermissionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='regularuser',
            email='user@example.com',
            password='userpass123'
        )
        self.client = Client()

    def test_admin_access_requires_superuser(self):
        """Test that only superusers can access admin"""
        # Try to access admin as regular user
        self.client.login(email='user@example.com', password='userpass123')
        url = reverse('admin:products_category_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_admin_access_with_superuser(self):
        """Test that superusers can access admin"""
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.client.login(email='admin@example.com', password='adminpass123')
        url = reverse('admin:products_category_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_admin_login_required(self):
        """Test that admin requires login"""
        url = reverse('admin:products_category_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login 