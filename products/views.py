from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Booking
from .forms import BookingForm
from django.db import IntegrityError

# List all active products (sessions)
def product_list(request):
    products = Product.objects.filter(is_active=True)
    return render(request, 'products/product_list.html', {'products': products})

# Show product detail and booking form
@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, is_active=True)
    if request.method == 'POST':
        form = BookingForm(request.POST, product=product)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.product = product
            booking.user = request.user
            try:
                booking.save()
                messages.success(request, 'Your session has been booked!')
                return redirect('bookings:booking_confirmation', pk=booking.pk)
            except IntegrityError:
                form.add_error(None, 'Sorry, this time slot is already booked. Please choose another.')
        else:
            print('DEBUG: form.errors =', form.errors)
            messages.error(request, 'There was an error with your booking. Please check the form and try again.')
    else:
        form = BookingForm(product=product)
    return render(request, 'products/product_detail.html', {'product': product, 'form': form})

# Booking confirmation view
@login_required
def booking_confirmation(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    return render(request, 'products/booking_confirmation.html', {'booking': booking})
