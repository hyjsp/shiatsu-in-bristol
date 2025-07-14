from django.db import models
from django.conf import settings

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_minutes = models.PositiveIntegerField(help_text='Session duration in minutes', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Booking(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bookings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    session_date = models.DateField()
    session_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    google_calendar_event_id = models.CharField(max_length=255, blank=True, null=True, help_text='Google Calendar event ID')

    class Meta:
        unique_together = ('session_date', 'session_time')

    def __str__(self):
        return f"{self.user} - {self.product} on {self.session_date} at {self.session_time}"
