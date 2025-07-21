#!/usr/bin/env python
"""
Simple test script to verify Google Calendar integration setup
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from calendar_integration.services import GoogleCalendarService

def test_calendar_service():
    """Test the calendar service setup"""
    print("Testing Google Calendar Service setup...")
    
    # Check if service account key exists
    if not os.path.exists('service-account-key.json'):
        print("❌ service-account-key.json not found in project root")
        print("Please create a service account in Google Cloud Console and download the key as 'service-account-key.json'")
        assert False, "service-account-key.json not found in project root"
    
    print("✅ service-account-key.json found")
    
    # Test service initialization
    try:
        service = GoogleCalendarService()
        print("✅ GoogleCalendarService initialized successfully")
        
        # Test authentication
        calendar_service = service.authenticate()
        if calendar_service:
            print("✅ Google Calendar API authentication successful")
        else:
            print("⚠️  Google Calendar API authentication failed - calendar integration will be disabled")
        assert calendar_service is not None, "Google Calendar API authentication failed"
    except Exception as e:
        print(f"❌ Error initializing service: {e}")
        assert False, f"Error initializing service: {e}"

if __name__ == "__main__":
    test_calendar_service() 