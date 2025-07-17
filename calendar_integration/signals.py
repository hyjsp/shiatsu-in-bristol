from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from products.models import Booking
from .services import GoogleCalendarService


@receiver(post_save, sender=Booking)
def create_or_update_calendar_event(sender, instance, created, **kwargs):
    """Create or update Google Calendar event when booking is saved"""
    try:
        # --- Prevent recursion: skip admin slots ---
        if getattr(instance, 'is_admin_slot', False):
            return
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
            try:
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
                print(f"[ERROR] Google Calendar update_event failed for booking {instance.pk}: {e}")
                # Do not crash the server
    except Exception as e:
        print(f"[ERROR] Calendar signal handler failed for booking {getattr(instance, 'pk', None)}: {e}")


@receiver(post_delete, sender=Booking)
def delete_calendar_event(sender, instance, **kwargs):
    print(f"[SIGNAL] post_delete fired for Booking pk={instance.pk}, user={getattr(instance.user, 'email', None)}, date={instance.session_date}, time={instance.session_time}")
    """Delete Google Calendar event when booking is deleted, including admin event. Log actions."""
    try:
        calendar_service = GoogleCalendarService()
        if instance.google_calendar_event_id:
            print(f"Deleting booking event from calendar: {instance.google_calendar_event_id}")
            calendar_service.delete_event(instance.google_calendar_event_id)
        else:
            print(f"No google_calendar_event_id to delete for booking {instance.pk}")
        if instance.admin_calendar_event_id:
            print(f"Deleting admin event from calendar: {instance.admin_calendar_event_id}")
            calendar_service.delete_event(instance.admin_calendar_event_id)
        else:
            print(f"No admin_calendar_event_id to delete for booking {instance.pk}")
    except Exception as e:
        print(f"Error deleting calendar event for booking {instance.pk}: {e}") 