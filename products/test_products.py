import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from datetime import time, timedelta
from django.contrib.auth import get_user_model
from .models import Category, Product, Booking
from .forms import BookingForm
from django.conf import settings

User = get_user_model()

# --- Fixtures ---
@pytest.fixture
def client():
    return Client()

@pytest.fixture
def user(transactional_db):
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def category(transactional_db):
    return Category.objects.create(name='Shiatsu Sessions')

@pytest.fixture
def listview_category(transactional_db):
    return Category.objects.create(name='ListView Category')

@pytest.fixture
def integration_category(transactional_db):
    return Category.objects.create(name='Integration Category')

@pytest.fixture
def product(transactional_db, category):
    return Product.objects.create(
        name='60-Minute Session',
        description='A relaxing 60-minute session',
        price=65.00,
        duration_minutes=60,
        category=category,
        is_active=True
    )

# --- Function-based view tests ---
def test_product_list_view(transactional_db, client, listview_category):
    product = Product.objects.create(
        name='ListViewProduct',
        description='Desc',
        price=10.0,
        duration_minutes=30,
        category=listview_category,
        is_active=True
    )
    response = client.get(reverse('products:product_list'))
    assert response.status_code == 200
    assert 'ListViewProduct' in response.content.decode()
    assert 'Book a Shiatsu Session' in response.content.decode()

def test_product_detail_view_authenticated(transactional_db, client, user, category):
    product = Product.objects.create(
        name='DetailProduct',
        description='Desc',
        price=20.0,
        duration_minutes=60,
        category=category,
        is_active=True
    )
    client.login(email='test@example.com', password='testpass123')
    response = client.get(reverse('products:product_detail', args=[product.pk]))
    assert response.status_code == 200
    assert 'DetailProduct' in response.content.decode()
    assert 'Book this session' in response.content.decode()

def test_product_detail_view_unauthenticated(transactional_db, client, category):
    product = Product.objects.create(
        name='UnauthProduct',
        description='Desc',
        price=30.0,
        duration_minutes=45,
        category=category,
        is_active=True
    )
    response = client.get(reverse('products:product_detail', args=[product.pk]))
    assert response.status_code == 302  # Redirect to login

def test_product_detail_view_invalid_pk(transactional_db, client, user):
    client.login(email='test@example.com', password='testpass123')
    response = client.get(reverse('products:product_detail', args=[999]))
    assert response.status_code == 404

def test_booking_creation_success(transactional_db, client, user, category):
    product = Product.objects.create(
        name='BookProduct',
        description='Desc',
        price=40.0,
        duration_minutes=90,
        category=category,
        is_active=True
    )
    client.login(email='test@example.com', password='testpass123')
    tomorrow = (timezone.now().date() + timedelta(days=1)).strftime('%Y-%m-%d')
    booking_data = {
        'session_date': tomorrow,
        'session_time': '14:00',
        'notes': 'Test booking'
    }
    response = client.post(
        reverse('products:product_detail', args=[product.pk]),
        booking_data
    )
    assert response.status_code == 302  # Redirect to confirmation
    booking = Booking.objects.first()
    assert booking is not None
    assert booking.product == product
    assert booking.user == user
    assert booking.notes == 'Test booking'

def test_booking_creation_invalid_data(transactional_db, client, user, category):
    product = Product.objects.create(
        name='InvalidBookProduct',
        description='Desc',
        price=50.0,
        duration_minutes=60,
        category=category,
        is_active=True
    )
    client.login(email='test@example.com', password='testpass123')
    yesterday = (timezone.now().date() - timedelta(days=1)).strftime('%Y-%m-%d')
    booking_data = {
        'session_date': yesterday,  # Past date
        'session_time': '14:00',
        'notes': 'Test booking'
    }
    response = client.post(
        reverse('products:product_detail', args=[product.pk]),
        booking_data
    )
    assert response.status_code == 200  # Form errors, stay on page
    assert Booking.objects.count() == 0

def test_booking_confirmation_view(transactional_db, client, user, category):
    product = Product.objects.create(
        name='ConfProduct',
        description='Desc',
        price=60.0,
        duration_minutes=75,
        category=category,
        is_active=True
    )
    client.login(email='test@example.com', password='testpass123')
    tomorrow = timezone.now().date() + timedelta(days=1)
    booking = Booking.objects.create(
        product=product,
        user=user,
        session_date=tomorrow,
        session_time=time(14, 0),
        notes='Test booking'
    )
    response = client.get(reverse('products:booking_confirmation', args=[booking.pk]))
    assert response.status_code == 200
    assert 'Booking Confirmed!' in response.content.decode()
    assert 'ConfProduct' in response.content.decode()

def test_booking_confirmation_view_wrong_user(transactional_db, client, user, category):
    other_user = User.objects.create_user(
        username='wronguser',
        email='wrong@example.com',
        password='testpass123'
    )
    product = Product.objects.create(
        name='WrongUserProduct',
        description='Desc',
        price=70.0,
        duration_minutes=80,
        category=category,
        is_active=True
    )
    client.login(email='wrong@example.com', password='testpass123')
    tomorrow = timezone.now().date() + timedelta(days=1)
    booking = Booking.objects.create(
        product=product,
        user=user,  # Created by different user
        session_date=tomorrow,
        session_time=time(14, 0),
        notes='Test booking'
    )
    response = client.get(reverse('products:booking_confirmation', args=[booking.pk]))
    assert response.status_code == 404  # Should not be accessible

# --- Integration test ---
# Moved to test_integration.py to avoid database state contamination
