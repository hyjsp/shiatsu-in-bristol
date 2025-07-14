from django.apps import AppConfig


class CalendarIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'calendar_integration'
    
    def ready(self):
        """Import signals when the app is ready"""
        import calendar_integration.signals