from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from products.models import Booking
from products.forms import BookingForm
from django.contrib import messages

# Create your views here.

@login_required
def profile(request):
    bookings = Booking.objects.filter(user=request.user).order_by('-session_date', '-session_time')
    return render(request, 'account/profile.html', {'bookings': bookings})

@login_required
def edit_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your booking has been updated successfully!')
            return redirect('account:profile')
    else:
        form = BookingForm(instance=booking)
    return render(request, 'account/edit_booking.html', {'form': form, 'booking': booking})

@login_required
def cancel_booking(request, pk):
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    if request.method == 'POST':
        booking.delete()
        messages.success(request, 'Your booking has been cancelled successfully!')
        return redirect('account:profile')
    return render(request, 'account/cancel_booking.html', {'booking': booking})
