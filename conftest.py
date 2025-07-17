import pytest
from datetime import timedelta, time
from django.utils import timezone
import uuid
from products.models import Booking, Product, Category
from accounts.models import CustomUser as User

created_event_ids = []

@pytest.fixture(autouse=True, scope="session")
def cleanup_google_calendar_events(request):
    """
    After the test session, delete all Google Calendar events created during tests.
    """
    from calendar_integration.services import GoogleCalendarService

    def cleanup():
        calendar_service = GoogleCalendarService()
        for event_id in created_event_ids:
            try:
                calendar_service.delete_event(event_id)
                print(f"[TEST CLEANUP] Deleted Google Calendar event: {event_id}")
            except Exception as e:
                print(f"[TEST CLEANUP] Failed to delete event {event_id}: {e}")

    request.addfinalizer(cleanup)

# Helper for unique booking slots
def unique_slot(test_name, offset=0):
    base_date = timezone.now().date() + timedelta(days=2 + abs(hash(test_name)) % 50 + offset)
    base_time = time(9 + (abs(hash(test_name)) % 8), 0)
    return base_date, base_time

@pytest.fixture
def booking(transactional_db, user, product):
    session_date, session_time = unique_slot('booking_fixture')
    notes = f'TEST_BOOKING_booking_fixture_{uuid.uuid4().hex[:8]}'
    b = Booking.objects.create(
        product=product,
        user=user,
        session_date=session_date,
        session_time=session_time,
        notes=notes
    )
    if hasattr(b, 'google_calendar_event_id') and b.google_calendar_event_id:
        created_event_ids.append(b.google_calendar_event_id)
    if hasattr(b, 'admin_calendar_event_id') and b.admin_calendar_event_id:
        created_event_ids.append(b.admin_calendar_event_id)
    return b 