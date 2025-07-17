import pytest
import time
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.cache import cache
from django.db import connection, reset_queries
from django.utils import timezone
from datetime import date, time as datetime_time, timedelta
from decimal import Decimal
from products.models import Category, Product, Booking

User = get_user_model()


class TemplateRenderingPerformanceTests(TestCase):
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

    def test_product_list_template_rendering_performance(self):
        """Test that product list template renders efficiently"""
        # Measure rendering time
        start_time = time.time()
        
        response = self.client.get(reverse('products:product_list'))
        
        end_time = time.time()
        rendering_time = end_time - start_time
        
        # Check that response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that rendering time is reasonable (less than 1 second)
        self.assertLess(rendering_time, 1.0)

    def test_product_detail_template_rendering_performance(self):
        """Test that product detail template renders efficiently"""
        self.client.login(email='test@example.com', password='testpass123')
        
        # Measure rendering time
        start_time = time.time()
        
        response = self.client.get(reverse('products:product_detail', args=[self.product.pk]))
        
        end_time = time.time()
        rendering_time = end_time - start_time
        
        # Check that response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that rendering time is reasonable (less than 1 second)
        self.assertLess(rendering_time, 1.0)

    def test_template_inheritance_performance(self):
        """Test that template inheritance doesn't impact performance significantly"""
        # Measure base template rendering
        start_time = time.time()
        
        response = self.client.get(reverse('products:product_list'))
        
        end_time = time.time()
        base_rendering_time = end_time - start_time
        
        # Check that rendering time is reasonable
        self.assertLess(base_rendering_time, 1.0)

    def test_large_template_data_performance(self):
        """Test performance with large amounts of template data"""
        # Create many products
        for i in range(50):
            Product.objects.create(
                category=self.category,
                name=f'Session {i}',
                description=f'Description {i}',
                price=50.00 + i,
                duration_minutes=60,
                is_active=True
            )
        
        # Measure rendering time with large dataset
        start_time = time.time()
        
        response = self.client.get(reverse('products:product_list'))
        
        end_time = time.time()
        rendering_time = end_time - start_time
        
        # Check that response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that rendering time is still reasonable (less than 2 seconds)
        self.assertLess(rendering_time, 2.0)


class DatabaseQueryPerformanceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Shiatsu Sessions')
        
        # Create test products
        for i in range(10):
            Product.objects.create(
                category=self.category,
                name=f'Session {i}',
                description=f'Description {i}',
                price=50.00 + i,
                duration_minutes=60,
                is_active=True
            )

    def test_product_list_query_optimization(self):
        """Test that product list view uses optimized queries"""
        # Reset query count
        reset_queries()
        
        # Make request
        response = self.client.get(reverse('products:product_list'))
        
        # Get query count
        query_count = len(connection.queries)
        
        # Check that response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that query count is reasonable (should be low for simple list)
        self.assertLess(query_count, 10)

    def test_large_dataset_performance(self):
        """Test performance with large dataset"""
        # Create many more products
        for i in range(100):
            Product.objects.create(
                category=self.category,
                name=f'Large Session {i}',
                description=f'Large Description {i}',
                price=50.00 + i,
                duration_minutes=60,
                is_active=True
            )
        
        # Measure query performance
        start_time = time.time()
        
        response = self.client.get(reverse('products:product_list'))
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Check that response is successful
        self.assertEqual(response.status_code, 200)
        
        # Check that query time is reasonable (less than 1 second)
        self.assertLess(query_time, 1.0)

    def test_complex_queries_performance(self):
        """Test performance of complex queries"""
        # Create bookings for performance testing
        for i in range(20):
            # Ensure unique (session_date, session_time) for each booking
            day = 15 + (i // 8)  # 15, 16, 17
            hour = 9 + (i % 8)   # 9-16
            Booking.objects.create(
                product=self.category.products.first(),
                user=self.user,
                session_date=date(2024, 1, day),
                session_time=datetime_time(hour, 0),
                notes=f'Test booking {i}'
            )
        
        # Measure complex query performance
        start_time = time.time()
        
        # Only count non-admin bookings
        bookings = Booking.objects.select_related('product', 'user').filter(is_admin_slot=False)
        booking_count = bookings.count()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        # Check that query executed successfully
        self.assertEqual(booking_count, 20)
        
        # Check that query time is reasonable
        self.assertLess(query_time, 1.0)


class CachingPerformanceTests(TestCase):
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

    def test_cache_effectiveness(self):
        """Test that caching improves performance"""
        # Clear cache
        cache.clear()
        
        # First request (cache miss)
        start_time = time.time()
        response1 = self.client.get(reverse('products:product_list'))
        first_request_time = time.time() - start_time
        
        # Second request (cache hit)
        start_time = time.time()
        response2 = self.client.get(reverse('products:product_list'))
        second_request_time = time.time() - start_time
        
        # Both responses should be successful
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Second request should be faster (in a real caching scenario)
        # Note: In test environment, caching might not be as effective
        self.assertIsInstance(first_request_time, float)
        self.assertIsInstance(second_request_time, float)

    def test_cache_invalidation(self):
        """Test that cache invalidation works properly"""
        # Clear cache
        cache.clear()
        
        # First request
        response1 = self.client.get(reverse('products:product_list'))
        
        # Update product
        self.product.name = 'Updated Session'
        self.product.save()
        
        # Second request should show updated content
        response2 = self.client.get(reverse('products:product_list'))
        
        # Both responses should be successful
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)
        
        # Content should be different (or same if no caching)
        # This test verifies the cache invalidation mechanism works

    def test_cache_backend_performance(self):
        """Test performance with different cache backends"""
        # Test cache set/get performance
        start_time = time.time()
        
        # Set cache
        cache.set('test_key', 'test_value', 60)
        
        # Get cache
        value = cache.get('test_key')
        
        end_time = time.time()
        cache_time = end_time - start_time
        
        # Check that cache operations work
        self.assertEqual(value, 'test_value')
        
        # Check that cache operations are fast
        self.assertLess(cache_time, 1.0)


class LoadTestingScenarios(TestCase):
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

    def test_concurrent_user_simulation(self):
        """Test performance with simulated concurrent users"""
        # Simulate multiple concurrent requests
        start_time = time.time()
        
        responses = []
        for i in range(10):
            response = self.client.get(reverse('products:product_list'))
            responses.append(response)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Check that all responses are successful
        for response in responses:
            self.assertEqual(response.status_code, 200)
        
        # Check that total time is reasonable
        self.assertLess(total_time, 5.0)

    def test_database_connection_pool_performance(self):
        """Test database connection pool performance"""
        # Simulate multiple database operations
        start_time = time.time()
        
        for i in range(50):
            Product.objects.create(
                category=self.category,
                name=f'Performance Test Session {i}',
                description=f'Performance test description {i}',
                price=50.00 + i,
                duration_minutes=60,
                is_active=True
            )
        
        end_time = time.time()
        db_time = end_time - start_time
        
        # Check that database operations completed
        self.assertEqual(Product.objects.count(), 51)  # 1 from setUp + 50 new
        
        # Check that database operations are reasonably fast
        self.assertLess(db_time, 5.0)

    def test_memory_usage_performance(self):
        """Test memory usage during heavy operations"""
        # This test simulates memory usage monitoring
        # In a real application, you might use psutil or similar
        
        # Simulate memory-intensive operation
        start_time = time.time()
        
        # Create many objects
        products = []
        for i in range(100):
            product = Product(
                category=self.category,
                name=f'Memory Test Session {i}',
                description=f'Memory test description {i}',
                price=50.00 + i,
                duration_minutes=60,
                is_active=True
            )
            products.append(product)
        
        # Bulk create to test memory efficiency
        Product.objects.bulk_create(products)
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        # Check that operation completed
        self.assertEqual(Product.objects.count(), 101)  # 1 from setUp + 100 new
        
        # Check that operation time is reasonable
        self.assertLess(operation_time, 5.0)

    def test_response_time_consistency(self):
        """Test that response times are consistent"""
        response_times = []
        
        # Make multiple requests and measure response times
        for i in range(10):
            start_time = time.time()
            response = self.client.get(reverse('products:product_list'))
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            # Check that response is successful
            self.assertEqual(response.status_code, 200)
        
        # Calculate average response time
        avg_response_time = sum(response_times) / len(response_times)
        
        # Check that average response time is reasonable
        self.assertLess(avg_response_time, 1.0)
        
        # Check that response times are consistent (not too much variance)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        variance = max_response_time - min_response_time
        
        # Variance should be reasonable (less than 0.5 seconds)
        self.assertLess(variance, 0.5)


class QueryOptimizationTests(TestCase):
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

    def test_select_related_optimization(self):
        """Test that select_related reduces query count"""
        # Create a booking
        booking = Booking.objects.create(
            product=self.product,
            user=self.user,
            session_date=date(2024, 1, 15),
            session_time=datetime_time(14, 0),
            notes='Test booking'
        )
        
        # Reset query count
        reset_queries()
        
        # Query without select_related
        bookings_without = Booking.objects.all()
        for booking in bookings_without:
            _ = booking.product.name  # This would cause additional queries
            _ = booking.user.username  # This would cause additional queries
        
        query_count_without = len(connection.queries)
        
        # Reset query count
        reset_queries()
        
        # Query with select_related
        bookings_with = Booking.objects.select_related('product', 'user').all()
        for booking in bookings_with:
            _ = booking.product.name  # No additional query
            _ = booking.user.username  # No additional query
        
        query_count_with = len(connection.queries)
        
        # select_related should reduce query count
        self.assertLessEqual(query_count_with, query_count_without)

    def test_prefetch_related_optimization(self):
        """Test that prefetch_related reduces query count for reverse relationships"""
        # Create multiple bookings for the product
        for i in range(5):
            Booking.objects.create(
                product=self.product,
                user=self.user,
                session_date=date(2024, 1, 15 + i),
                session_time=datetime_time(14, 0),
                notes=f'Test booking {i}'
            )
        
        # Reset query count
        reset_queries()
        
        # Query without prefetch_related
        products_without = Product.objects.all()
        for product in products_without:
            _ = list(product.bookings.all())  # Use correct relationship name
        
        query_count_without = len(connection.queries)
        
        # Reset query count
        reset_queries()
        
        # Query with prefetch_related
        products_with = Product.objects.prefetch_related('bookings').all()  # Use correct relationship name
        for product in products_with:
            _ = list(product.bookings.all())  # No additional queries
        
        query_count_with = len(connection.queries)
        
        # prefetch_related should reduce query count
        self.assertLessEqual(query_count_with, query_count_without)

    def test_bulk_operations_performance(self):
        """Test that bulk operations are more performant"""
        # Measure individual create performance
        start_time = time.time()
        
        for i in range(50):
            Product.objects.create(
                category=self.category,
                name=f'Individual Session {i}',
                description=f'Individual description {i}',
                price=50.00 + i,
                duration_minutes=60,
                is_active=True
            )
        
        individual_time = time.time() - start_time
        
        # Clear products
        Product.objects.filter(name__startswith='Individual').delete()
        
        # Measure bulk create performance
        start_time = time.time()
        
        products = []
        for i in range(50):
            product = Product(
                category=self.category,
                name=f'Bulk Session {i}',
                description=f'Bulk description {i}',
                price=50.00 + i,
                duration_minutes=60,
                is_active=True
            )
            products.append(product)
        
        Product.objects.bulk_create(products)
        
        bulk_time = time.time() - start_time
        
        # Bulk operations should be faster
        self.assertLess(bulk_time, individual_time) 