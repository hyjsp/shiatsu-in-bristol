import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, time
from products.models import Product, Category, Booking
from accounts.models import CustomUser


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user(transactional_db):
    return CustomUser.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def integration_category(transactional_db):
    return Category.objects.create(name='Integration Category')


@pytest.mark.skip(reason="Database isolation issues when running with full test suite - run separately")
def test_complete_booking_flow(transactional_db, client, user, integration_category):
    # Clear any products from previous tests
    Product.objects.all().delete()
    
    product = Product.objects.create(
        name='Integration Test Session',
        description='A relaxing 60-minute session',
        price=65.00,
        duration_minutes=60,
        category=integration_category,
        is_active=True
    )
    # 1. User visits product list
    response = client.get(reverse('products:product_list'))
    assert response.status_code == 200
    assert 'Integration Test Session' in response.content.decode()

    # 2. User clicks on product (simulated by visiting detail page)
    client.login(email='test@example.com', password='testpass123')
    response = client.get(reverse('products:product_detail', args=[product.pk]))
    assert response.status_code == 200
    assert 'Book this session' in response.content.decode()

    # 3. User submits booking form
    tomorrow = (timezone.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
    booking_data = {
        'session_date': tomorrow,
        'session_time': '14:00',
        'notes': 'Please bring a towel'
    }
    response = client.post(
        reverse('products:product_detail', args=[product.pk]),
        booking_data
    )
    assert response.status_code == 302  # Redirect to confirmation

    # 4. Check booking was created
    booking = Booking.objects.first()
    assert booking is not None
    assert booking.product == product
    assert booking.user == user
    assert booking.notes == 'Please bring a towel'

    # 5. User sees confirmation page
    response = client.get(reverse('products:booking_confirmation', args=[booking.pk]))
    assert response.status_code == 200
    assert 'Booking Confirmed!' in response.content.decode()
    assert 'Integration Test Session' in response.content.decode() 