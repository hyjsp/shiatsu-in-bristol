import os
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings
from django.core.cache import cache
import pickle


class GoogleCalendarService:
    """Service for handling Google Calendar operations using Service Account"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    CALENDAR_ID = 'b13185473c296c9746f105b2f5fb5a9191598cfcab898dc20ce9b3d7f6cb1a5e@group.calendar.google.com'  # Use your shared calendar's email address
    
    def __init__(self):
        self.service = None
    
    def authenticate(self):
        """Authenticate with Google Calendar API using Service Account"""
        try:
            # Use service account credentials
            if os.path.exists('service-account-key.json'):
                credentials = service_account.Credentials.from_service_account_file(
                    'service-account-key.json', scopes=self.SCOPES)
                self.service = build('calendar', 'v3', credentials=credentials)
                return self.service
            else:
                print("Warning: service-account-key.json not found. Calendar integration will be disabled.")
                return None
        except Exception as e:
            print(f"Error authenticating with Google Calendar: {e}")
            return None
    
    def create_event(self, booking):
        """Create a calendar event for a booking and a 30-min admin break after it. Save both event IDs directly on the instance."""
        try:
            if not self.service:
                self.authenticate()
                if not self.service:
                    return None
            # --- Prevent recursion: skip admin slot bookings ---
            if getattr(booking, 'is_admin_slot', False):
                return None
            # Calculate session start and end
            session_start = datetime.combine(booking.session_date, booking.session_time)
            session_end = session_start + timedelta(minutes=booking.product.duration_minutes or 60)
            # Format the event details for the booking
            event = {
                'summary': f'Shiatsu Session - {booking.product.name}',
                'description': f'Client: {booking.user.get_full_name() or booking.user.email}\nNotes: {booking.notes}',
                'start': {
                    'dateTime': session_start.strftime('%Y-%m-%dT%H:%M:00'),
                    'timeZone': 'Europe/London',
                },
                'end': {
                    'dateTime': session_end.strftime('%Y-%m-%dT%H:%M:00'),
                    'timeZone': 'Europe/London',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 60},  # 1 hour before
                    ],
                },
            }
            event = self.service.events().insert(
                calendarId=self.CALENDAR_ID, 
                body=event
            ).execute()
            event_id = event.get('id')
            print(f"Created booking event with ID: {event_id}")
            # --- Only create admin slot and event for non-admin bookings ---
            admin_start = session_end
            admin_end = admin_start + timedelta(minutes=30)
            admin_event = {
                'summary': 'Admin',
                'description': f'Admin break after session for {booking.user.get_full_name() or booking.user.email}',
                'start': {
                    'dateTime': admin_start.strftime('%Y-%m-%dT%H:%M:00'),
                    'timeZone': 'Europe/London',
                },
                'end': {
                    'dateTime': admin_end.strftime('%Y-%m-%dT%H:%M:00'),
                    'timeZone': 'Europe/London',
                },
            }
            admin_event = self.service.events().insert(
                calendarId=self.CALENDAR_ID,
                body=admin_event
            ).execute()
            admin_event_id = admin_event.get('id')
            print(f"Created admin event with ID: {admin_event_id}")
            # Save both event IDs directly on the instance
            booking.google_calendar_event_id = event_id
            booking.admin_calendar_event_id = admin_event_id
            booking.save(update_fields=["google_calendar_event_id", "admin_calendar_event_id"])
            # --- Create a Booking instance for the admin slot in the DB ---
            from products.models import Booking as ProductBooking
            ProductBooking.objects.create(
                product=booking.product,
                user=booking.user,
                session_date=admin_start.date(),
                session_time=admin_start.time(),
                notes=f'Admin slot after session for {booking.user.get_full_name() or booking.user.email}',
                is_admin_slot=True
            )
            return event_id
        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return None
    
    def update_event(self, booking, event_id):
        """Update an existing calendar event"""
        try:
            if not self.service:
                self.authenticate()
                if not self.service:
                    return None
            
            event = {
                'summary': f'Shiatsu Session - {booking.product.name}',
                'description': f'Client: {booking.user.get_full_name() or booking.user.email}\nNotes: {booking.notes}',
                'start': {
                    'dateTime': f'{booking.session_date}T{booking.session_time.strftime("%H:%M")}:00',
                    'timeZone': 'Europe/London',
                },
                'end': {
                    'dateTime': f'{booking.session_date}T{(datetime.combine(booking.session_date, booking.session_time) + timedelta(minutes=booking.product.duration_minutes or 60)).strftime("%H:%M")}:00',
                    'timeZone': 'Europe/London',
                },
            }
            
            updated_event = self.service.events().update(
                calendarId=self.CALENDAR_ID,
                eventId=event_id,
                body=event
            ).execute()
            
            return updated_event
            
        except Exception as e:
            print(f"Error updating calendar event: {e}")
            return None
    
    def delete_event(self, event_id):
        """Delete a calendar event"""
        try:
            if not self.service:
                self.authenticate()
                if not self.service:
                    return False
            
            self.service.events().delete(
                calendarId=self.CALENDAR_ID,
                eventId=event_id
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"Error deleting calendar event: {e}")
            return False
    
    def check_availability(self, date, time, duration_minutes=60):
        """Check if a time slot is available"""
        try:
            if not self.service:
                self.authenticate()
                if not self.service:
                    return True  # Assume available if we can't check
            
            # Convert to datetime objects
            start_time = datetime.combine(date, time)
            end_time = start_time + timedelta(minutes=duration_minutes)
            
            # Query for events in the time slot
            events_result = self.service.events().list(
                calendarId=self.CALENDAR_ID,
                timeMin=start_time.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # If no events found, the slot is available
            return len(events) == 0
            
        except Exception as e:
            print(f"Error checking availability: {e}")
            return True  # Assume available if we can't check 