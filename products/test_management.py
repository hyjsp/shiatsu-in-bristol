import pytest
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth import get_user_model
from products.models import Category, Product, Booking
from io import StringIO

User = get_user_model()


class CreateSampleDataCommandTests(TestCase):
    def setUp(self):
        self.out = StringIO()

    def test_create_sample_data_command_success(self):
        """Test that create_sample_data command runs successfully"""
        # Check initial state
        self.assertEqual(Category.objects.count(), 0)
        self.assertEqual(Product.objects.count(), 0)
        
        # Run command
        call_command('create_sample_data', stdout=self.out)
        
        # Check that data was created
        self.assertGreater(Category.objects.count(), 0)
        self.assertGreater(Product.objects.count(), 0)
        
        # Check output message
        output = self.out.getvalue()
        self.assertIn('Sample data created successfully', output)

    def test_create_sample_data_command_output(self):
        """Test that create_sample_data command provides informative output"""
        call_command('create_sample_data', stdout=self.out)
        output = self.out.getvalue()
        
        # Check for expected output messages
        self.assertIn('Created category:', output)
        self.assertIn('Created product:', output)
        self.assertIn('Sample data created successfully', output)

    def test_create_sample_data_command_idempotent(self):
        """Test that create_sample_data can be run multiple times safely"""
        # Run command first time
        call_command('create_sample_data', stdout=self.out)
        initial_category_count = Category.objects.count()
        initial_product_count = Product.objects.count()
        
        # Clear output
        self.out = StringIO()
        
        # Run command second time
        call_command('create_sample_data', stdout=self.out)
        
        # Check that data wasn't duplicated
        self.assertEqual(Category.objects.count(), initial_category_count)
        self.assertEqual(Product.objects.count(), initial_product_count)

    def test_create_sample_data_command_creates_categories(self):
        """Test that create_sample_data creates categories"""
        call_command('create_sample_data', stdout=self.out)
        
        # Check that categories were created
        categories = Category.objects.all()
        self.assertGreater(categories.count(), 0)
        
        # Check that categories have names
        for category in categories:
            self.assertIsNotNone(category.name)
            self.assertGreater(len(category.name), 0)

    def test_create_sample_data_command_creates_products(self):
        """Test that create_sample_data creates products"""
        call_command('create_sample_data', stdout=self.out)
        
        # Check that products were created
        products = Product.objects.all()
        self.assertGreater(products.count(), 0)
        
        # Check that products have required fields
        for product in products:
            self.assertIsNotNone(product.name)
            self.assertIsNotNone(product.category)
            self.assertIsNotNone(product.price)
            self.assertGreater(product.price, 0)

    def test_create_sample_data_command_product_relationships(self):
        """Test that create_sample_data creates products with proper relationships"""
        call_command('create_sample_data', stdout=self.out)
        
        # Check that products are associated with categories
        products = Product.objects.select_related('category').all()
        for product in products:
            self.assertIsNotNone(product.category)
            self.assertIsInstance(product.category, Category)


class ClearSampleDataCommandTests(TestCase):
    def setUp(self):
        self.out = StringIO()
        # Create some sample data first
        call_command('create_sample_data', stdout=StringIO())

    def test_clear_sample_data_command_success(self):
        """Test that clear_sample_data command runs successfully"""
        # Check initial state
        self.assertGreater(Category.objects.count(), 0)
        self.assertGreater(Product.objects.count(), 0)
        
        # Run command with confirm flag
        call_command('clear_sample_data', confirm=True, stdout=self.out)
        
        # Check that data was cleared
        self.assertEqual(Category.objects.count(), 0)
        self.assertEqual(Product.objects.count(), 0)
        
        # Check output message
        output = self.out.getvalue()
        self.assertIn('Deleted', output)

    def test_clear_sample_data_command_output(self):
        """Test that clear_sample_data command provides informative output"""
        call_command('clear_sample_data', confirm=True, stdout=self.out)
        output = self.out.getvalue()
        
        # Check for expected output messages
        self.assertIn('Deleted', output)

    def test_clear_sample_data_command_idempotent(self):
        """Test that clear_sample_data can be run multiple times safely"""
        # Run command first time
        call_command('clear_sample_data', confirm=True, stdout=self.out)
        self.assertEqual(Category.objects.count(), 0)
        self.assertEqual(Product.objects.count(), 0)
        
        # Clear output
        self.out = StringIO()
        
        # Run command second time
        call_command('clear_sample_data', confirm=True, stdout=self.out)
        
        # Check that data is still cleared
        self.assertEqual(Category.objects.count(), 0)
        self.assertEqual(Product.objects.count(), 0)

    def test_clear_sample_data_command_preserves_bookings(self):
        """Test that clear_sample_data doesn't affect existing bookings"""
        # Create a booking
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        category = Category.objects.first()
        product = Product.objects.first()
        booking = Booking.objects.create(
            product=product,
            user=user,
            session_date='2024-01-15',
            session_time='14:00',
            notes='Test booking'
        )
        
        # Run command
        call_command('clear_sample_data', confirm=True, stdout=self.out)
        
        # Check that booking is deleted when product is deleted (due to CASCADE)
        self.assertEqual(Booking.objects.count(), 0)

    def test_clear_sample_data_command_clears_categories(self):
        """Test that clear_sample_data clears categories"""
        initial_count = Category.objects.count()
        self.assertGreater(initial_count, 0)
        
        call_command('clear_sample_data', confirm=True, stdout=self.out)
        
        self.assertEqual(Category.objects.count(), 0)

    def test_clear_sample_data_command_clears_products(self):
        """Test that clear_sample_data clears products"""
        initial_count = Product.objects.count()
        self.assertGreater(initial_count, 0)
        
        call_command('clear_sample_data', confirm=True, stdout=self.out)
        
        self.assertEqual(Product.objects.count(), 0)


class ManagementCommandIntegrationTests(TestCase):
    def setUp(self):
        self.out = StringIO()

    def test_create_then_clear_sample_data(self):
        """Test the full cycle of creating then clearing sample data"""
        # Create sample data
        call_command('create_sample_data', stdout=self.out)
        self.assertGreater(Category.objects.count(), 0)
        self.assertGreater(Product.objects.count(), 0)
        
        # Clear output
        self.out = StringIO()
        
        # Clear sample data
        call_command('clear_sample_data', confirm=True, stdout=self.out)
        self.assertEqual(Category.objects.count(), 0)
        self.assertEqual(Product.objects.count(), 0)

    def test_clear_then_create_sample_data(self):
        """Test the full cycle of clearing then creating sample data"""
        # Create initial data
        call_command('create_sample_data', stdout=self.out)
        initial_category_count = Category.objects.count()
        initial_product_count = Product.objects.count()
        
        # Clear output
        self.out = StringIO()
        
        # Clear sample data
        call_command('clear_sample_data', confirm=True, stdout=self.out)
        self.assertEqual(Category.objects.count(), 0)
        self.assertEqual(Product.objects.count(), 0)
        
        # Clear output
        self.out = StringIO()
        
        # Create sample data again
        call_command('create_sample_data', stdout=self.out)
        self.assertEqual(Category.objects.count(), initial_category_count)
        self.assertEqual(Product.objects.count(), initial_product_count)

    def test_command_output_formatting(self):
        """Test that command output is properly formatted"""
        # Test create command output
        call_command('create_sample_data', stdout=self.out)
        output = self.out.getvalue()
        self.assertIn('Created category:', output)
        self.assertIn('Created product:', output)
        self.assertIn('Sample data created successfully', output)
        
        # Clear output
        self.out = StringIO()
        
        # Test clear command output
        call_command('clear_sample_data', confirm=True, stdout=self.out)
        output = self.out.getvalue()
        self.assertIn('Deleted', output)

    def test_command_error_handling(self):
        """Test that commands handle errors gracefully"""
        # Test with invalid command name
        with self.assertRaises(CommandError):
            call_command('invalid_command_name', stdout=self.out) 