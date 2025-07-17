from django.contrib import admin
from .models import Category, Product, Booking
from django.db import IntegrityError
from django.contrib import messages

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'duration_minutes', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'session_date', 'session_time', 'created_at', 'status']
    list_filter = ['session_date', 'product', 'status']
    search_fields = ['user__email', 'product__name']

    actions = ['approve_bookings', 'deny_bookings', 'mark_reschedule', 'mark_refund']

    def approve_bookings(self, request, queryset):
        if not (request.user.is_staff or request.user.is_superuser):
            self.message_user(request, "You do not have permission to approve bookings.", level=messages.ERROR)
            return
        updated = queryset.update(status='approved')
        self.message_user(request, f"{updated} booking(s) marked as approved.")
    approve_bookings.short_description = "Approve selected bookings"

    def deny_bookings(self, request, queryset):
        updated = queryset.update(status='denied')
        self.message_user(request, f"{updated} booking(s) marked as denied.")
    deny_bookings.short_description = "Deny selected bookings"

    def mark_reschedule(self, request, queryset):
        if not (request.user.is_staff or request.user.is_superuser):
            self.message_user(request, "You do not have permission to reschedule bookings.", level=messages.ERROR)
            return
        updated = queryset.update(status='reschedule')
        self.message_user(request, f"{updated} booking(s) marked as reschedule.")
    mark_reschedule.short_description = "Mark selected bookings as reschedule"

    def mark_refund(self, request, queryset):
        if not (request.user.is_staff or request.user.is_superuser):
            self.message_user(request, "You do not have permission to refund bookings.", level=messages.ERROR)
            return
        updated = queryset.update(status='refund')
        self.message_user(request, f"{updated} booking(s) marked as refund.")
    mark_refund.short_description = "Mark selected bookings as refund"

    def save_model(self, request, obj, form, change):
        try:
            super().save_model(request, obj, form, change)
        except IntegrityError:
            self.message_user(request, "A booking already exists for this date and time. Please choose another slot.", level=messages.ERROR)
