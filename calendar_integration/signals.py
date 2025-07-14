from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from products.models import Booking
from .services import GoogleCalendarService


@receiver(post_save, sender=Booking)
def create_or_update_calendar_event(sender, instance, created, **kwargs):
    """Create or update Google Calendar event when booking is saved"""
    try:
        calendar_service = GoogleCalendarService()
        
        if created:
            # Create new calendar event
            event_id = calendar_service.create_event(instance)
            if event_id:
                # Update the booking with the event ID
                instance.google_calendar_event_id = event_id
                # Save without triggering the signal again
                Booking.objects.filter(pk=instance.pk).update(
                    google_calendar_event_id=event_id
                )
        else:
            # Update existing calendar event
            if instance.google_calendar_event_id:
                calendar_service.update_event(instance, instance.google_calendar_event_id)
            else:
                # If no event ID exists, create a new event
                event_id = calendar_service.create_event(instance)
                if event_id:
                    instance.google_calendar_event_id = event_id
                    # Save without triggering the signal again
                    Booking.objects.filter(pk=instance.pk).update(
                        google_calendar_event_id=event_id
                    )
                    
    except Exception as e:
        print(f"Error handling calendar event for booking {instance.pk}: {e}")


@receiver(post_delete, sender=Booking)
def delete_calendar_event(sender, instance, **kwargs):
    """Delete Google Calendar event when booking is deleted"""
    try:
        if instance.google_calendar_event_id:
            calendar_service = GoogleCalendarService()
            calendar_service.delete_event(instance.google_calendar_event_id)
    except Exception as e:
        print(f"Error deleting calendar event for booking {instance.pk}: {e}") 