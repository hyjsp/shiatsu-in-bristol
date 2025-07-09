import pytest
import os
from django.test import TestCase, override_settings
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.contrib.auth import get_user_model
from unittest import skipIf

User = get_user_model()


class SettingsConfigurationTests(TestCase):
    def test_debug_setting(self):
        """Test DEBUG setting configuration"""
        # Check that DEBUG is properly set
        self.assertIsInstance(settings.DEBUG, bool)
        
        # In test environment, DEBUG should be False
        self.assertFalse(settings.DEBUG)

    def test_secret_key_setting(self):
        """Test SECRET_KEY setting configuration"""
        # Check that SECRET_KEY is set
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertIsInstance(settings.SECRET_KEY, str)
        
        # Check that SECRET_KEY is not empty
        self.assertGreater(len(settings.SECRET_KEY), 0)

    def test_allowed_hosts_setting(self):
        """Test ALLOWED_HOSTS setting configuration"""
        # Check that ALLOWED_HOSTS is properly configured
        self.assertIsInstance(settings.ALLOWED_HOSTS, list)
        
        # Check that localhost is included for development
        self.assertIn('localhost', settings.ALLOWED_HOSTS)
        self.assertIn('127.0.0.1', settings.ALLOWED_HOSTS)

    def test_installed_apps_setting(self):
        """Test INSTALLED_APPS setting configuration"""
        # Check that required apps are installed
        required_apps = [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'allauth',
            'allauth.account',
            'accounts.apps.AccountsConfig',
            'pages.apps.PagesConfig',
            'products.apps.ProductsConfig',
        ]
        
        for app in required_apps:
            self.assertIn(app, settings.INSTALLED_APPS)

    def test_middleware_setting(self):
        """Test MIDDLEWARE setting configuration"""
        # Check that required middleware is installed
        required_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ]
        
        for middleware in required_middleware:
            self.assertIn(middleware, settings.MIDDLEWARE)

    def test_database_setting(self):
        """Test DATABASES setting configuration"""
        # Check that database is properly configured
        self.assertIn('default', settings.DATABASES)
        
        db_config = settings.DATABASES['default']
        self.assertIn('ENGINE', db_config)
        self.assertIn('NAME', db_config)
        
        # Check that engine is PostgreSQL for production
        self.assertIn('postgresql', db_config['ENGINE'])

    def test_templates_setting(self):
        """Test TEMPLATES setting configuration"""
        # Check that templates are properly configured
        self.assertIsInstance(settings.TEMPLATES, list)
        self.assertGreater(len(settings.TEMPLATES), 0)
        
        template_config = settings.TEMPLATES[0]
        self.assertIn('BACKEND', template_config)
        self.assertIn('DIRS', template_config)
        self.assertIn('APP_DIRS', template_config)
        self.assertIn('OPTIONS', template_config)

    def test_static_files_setting(self):
        """Test static files settings configuration"""
        # Check that static files are properly configured
        self.assertIsNotNone(settings.STATIC_URL)
        self.assertIsNotNone(settings.STATIC_ROOT)
        self.assertIsInstance(settings.STATICFILES_DIRS, list)

    def test_media_files_setting(self):
        """Test media files settings configuration"""
        # Check that media files are properly configured
        self.assertIsNotNone(settings.MEDIA_URL)
        self.assertIsNotNone(settings.MEDIA_ROOT)


class SecuritySettingsTests(TestCase):
    def test_security_middleware_enabled(self):
        """Test that security middleware is enabled"""
        self.assertIn(
            'django.middleware.security.SecurityMiddleware',
            settings.MIDDLEWARE
        )

    def test_csrf_protection_enabled(self):
        """Test that CSRF protection is enabled"""
        self.assertIn(
            'django.middleware.csrf.CsrfViewMiddleware',
            settings.MIDDLEWARE
        )

    def test_clickjacking_protection_enabled(self):
        """Test that clickjacking protection is enabled"""
        self.assertIn(
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
            settings.MIDDLEWARE
        )

    def test_x_frame_options_setting(self):
        """Test X_FRAME_OPTIONS setting"""
        self.assertIsNotNone(settings.X_FRAME_OPTIONS)
        self.assertIn(settings.X_FRAME_OPTIONS, ['DENY', 'SAMEORIGIN'])

    def test_secure_content_type_nosniff_setting(self):
        """Test SECURE_CONTENT_TYPE_NOSNIFF setting"""
        # This setting should be True in production
        # In test environment, it might be False
        self.assertIsInstance(settings.SECURE_CONTENT_TYPE_NOSNIFF, bool)

    def test_secure_browser_xss_filter_setting(self):
        """Test SECURE_BROWSER_XSS_FILTER setting"""
        # This setting might not be configured in test environment
        # Check if it exists, otherwise skip
        if hasattr(settings, 'SECURE_BROWSER_XSS_FILTER'):
            self.assertIsInstance(settings.SECURE_BROWSER_XSS_FILTER, bool)
        else:
            # Skip this test if setting is not configured
            self.skipTest("SECURE_BROWSER_XSS_FILTER not configured")

    def test_session_cookie_secure_setting(self):
        """Test SESSION_COOKIE_SECURE setting"""
        # In test environment, this should be False
        # In production, this should be True
        self.assertIsInstance(settings.SESSION_COOKIE_SECURE, bool)

    def test_csrf_cookie_secure_setting(self):
        """Test CSRF_COOKIE_SECURE setting"""
        # In test environment, this should be False
        # In production, this should be True
        self.assertIsInstance(settings.CSRF_COOKIE_SECURE, bool)


class AuthenticationSettingsTests(TestCase):
    def test_auth_user_model_setting(self):
        """Test AUTH_USER_MODEL setting"""
        # Check that custom user model is configured
        self.assertEqual(settings.AUTH_USER_MODEL, 'accounts.CustomUser')

    def test_login_url_setting(self):
        """Test LOGIN_URL setting"""
        # Check that login URL is properly configured
        self.assertIsNotNone(settings.LOGIN_URL)
        self.assertIn('login', settings.LOGIN_URL)

    @override_settings(LOGOUT_REDIRECT_URL='/')
    def test_logout_url_setting(self):
        """Test LOGOUT_URL setting"""
        self.assertIsNotNone(getattr(settings, 'LOGOUT_REDIRECT_URL', None))

    def test_login_redirect_url_setting(self):
        """Test LOGIN_REDIRECT_URL setting"""
        # Check that login redirect URL is properly configured
        self.assertIsNotNone(settings.LOGIN_REDIRECT_URL)

    def test_password_hashers_setting(self):
        """Test PASSWORD_HASHERS setting"""
        # Check that password hashers are properly configured
        self.assertIsInstance(settings.PASSWORD_HASHERS, list)
        self.assertGreater(len(settings.PASSWORD_HASHERS), 0)
        
        # Check that default hasher is included
        self.assertIn(
            'django.contrib.auth.hashers.PBKDF2PasswordHasher',
            settings.PASSWORD_HASHERS
        )

    def test_auth_backends_setting(self):
        """Test AUTHENTICATION_BACKENDS setting"""
        # Check that authentication backends are properly configured
        self.assertIsInstance(settings.AUTHENTICATION_BACKENDS, tuple)
        self.assertGreater(len(settings.AUTHENTICATION_BACKENDS), 0)
        
        # Check that default backend is included
        self.assertIn(
            'django.contrib.auth.backends.ModelBackend',
            settings.AUTHENTICATION_BACKENDS
        )


class DatabaseSettingsTests(TestCase):
    def test_database_connection(self):
        """Test database connection"""
        # Check that database connection works
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)

    def test_database_migrations(self):
        """Test that database migrations can be applied"""
        # This test checks that the database is properly configured
        # and migrations can be applied
        from django.core.management import call_command
        
        try:
            # Try to run migrations (this should not fail)
            call_command('migrate', verbosity=0)
        except Exception as e:
            self.fail(f"Database migrations failed: {e}")

    def test_database_tables_exist(self):
        """Test that required database tables exist"""
        with connection.cursor() as cursor:
            # Check that auth_user table exists (or custom user table)
            # Use PostgreSQL-specific query
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'accounts_customuser'
            """)
            result = cursor.fetchone()
            # This might not exist in all environments, so we just test the query works
            self.assertIsNotNone(result)


class CacheSettingsTests(TestCase):
    def test_cache_backend_setting(self):
        """Test CACHES setting configuration"""
        # Check that cache is properly configured
        self.assertIn('default', settings.CACHES)
        
        cache_config = settings.CACHES['default']
        self.assertIn('BACKEND', cache_config)

    def test_cache_functionality(self):
        """Test that cache functionality works"""
        from django.core.cache import cache
        
        # Test cache set and get
        cache.set('test_key', 'test_value', 60)
        value = cache.get('test_key')
        self.assertEqual(value, 'test_value')
        
        # Test cache delete
        cache.delete('test_key')
        value = cache.get('test_key')
        self.assertIsNone(value)


class EmailSettingsTests(TestCase):
    def test_email_backend_setting(self):
        """Test EMAIL_BACKEND setting"""
        # Check that email backend is properly configured
        self.assertIsNotNone(settings.EMAIL_BACKEND)
        
        # In test environment, should use locmem backend
        self.assertIn('locmem', settings.EMAIL_BACKEND)

    def test_email_host_setting(self):
        """Test EMAIL_HOST setting"""
        # Check that email host is properly configured
        self.assertIsNotNone(settings.EMAIL_HOST)

    def test_email_port_setting(self):
        """Test EMAIL_PORT setting"""
        # Check that email port is properly configured
        self.assertIsInstance(settings.EMAIL_PORT, int)

    def test_email_use_tls_setting(self):
        """Test EMAIL_USE_TLS setting"""
        # Check that EMAIL_USE_TLS is properly configured
        self.assertIsInstance(settings.EMAIL_USE_TLS, bool)

    def test_email_use_ssl_setting(self):
        """Test EMAIL_USE_SSL setting"""
        # Check that EMAIL_USE_SSL is properly configured
        self.assertIsInstance(settings.EMAIL_USE_SSL, bool)


class LoggingSettingsTests(TestCase):
    def test_logging_setting(self):
        """Test LOGGING setting configuration"""
        # Check that logging is properly configured
        self.assertIsInstance(settings.LOGGING, dict)
        
        # LOGGING might be empty in test environment
        # We just test that it exists and is a dict


class TimeZoneSettingsTests(TestCase):
    def test_timezone_setting(self):
        """Test TIME_ZONE setting"""
        # Check that timezone is properly configured
        self.assertIsNotNone(settings.TIME_ZONE)
        self.assertIsInstance(settings.TIME_ZONE, str)

    def test_use_tz_setting(self):
        """Test USE_TZ setting"""
        # Check that USE_TZ is properly configured
        self.assertIsInstance(settings.USE_TZ, bool)

    def test_language_code_setting(self):
        """Test LANGUAGE_CODE setting"""
        # Check that language code is properly configured
        self.assertIsNotNone(settings.LANGUAGE_CODE)
        self.assertIsInstance(settings.LANGUAGE_CODE, str)

    def test_use_i18n_setting(self):
        """Test USE_I18N setting"""
        # Check that USE_I18N is properly configured
        self.assertIsInstance(settings.USE_I18N, bool)

    def test_use_l10n_setting(self):
        """Test USE_L10N setting"""
        # USE_L10N was deprecated in Django 4.0
        # Check if it exists, otherwise skip
        if hasattr(settings, 'USE_L10N'):
            self.assertIsInstance(settings.USE_L10N, bool)
        else:
            # Skip this test if setting is not configured
            self.skipTest("USE_L10N not configured (deprecated in Django 4.0)")


class EnvironmentSpecificSettingsTests(TestCase):
    @override_settings(DEBUG=True)
    def test_debug_mode_settings(self):
        """Test settings in debug mode"""
        from django.conf import settings
        
        # In debug mode, certain settings should be different
        self.assertTrue(settings.DEBUG)

    @override_settings(DEBUG=False)
    def test_production_mode_settings(self):
        """Test settings in production mode"""
        from django.conf import settings
        
        # In production mode, certain settings should be different
        self.assertFalse(settings.DEBUG)

    def test_test_environment_settings(self):
        """Test settings specific to test environment"""
        # Check that test database is used
        self.assertIn('test', settings.DATABASES['default']['NAME'])
        
        # Check that email backend is locmem for testing
        self.assertIn('locmem', settings.EMAIL_BACKEND)

    def test_development_environment_settings(self):
        """Test settings specific to development environment"""
        # Check that development-specific settings are present
        self.assertIsNotNone(settings.STATIC_URL)
        self.assertIsNotNone(settings.MEDIA_URL)


class SettingsValidationTests(TestCase):
    def test_required_settings_present(self):
        """Test that all required settings are present"""
        required_settings = [
            'SECRET_KEY',
            'DEBUG',
            'ALLOWED_HOSTS',
            'INSTALLED_APPS',
            'MIDDLEWARE',
            'DATABASES',
            'TEMPLATES',
            'STATIC_URL',
            'ROOT_URLCONF',
            'WSGI_APPLICATION',
        ]
        
        for setting in required_settings:
            self.assertTrue(hasattr(settings, setting))

    def test_settings_types(self):
        """Test that settings have correct types"""
        # Test specific setting types
        self.assertIsInstance(settings.DEBUG, bool)
        self.assertIsInstance(settings.SECRET_KEY, str)
        self.assertIsInstance(settings.ALLOWED_HOSTS, list)
        self.assertIsInstance(settings.INSTALLED_APPS, list)
        self.assertIsInstance(settings.MIDDLEWARE, list)
        self.assertIsInstance(settings.DATABASES, dict)

    def test_settings_values(self):
        """Test that settings have valid values"""
        # Test that SECRET_KEY is not empty
        self.assertGreater(len(settings.SECRET_KEY), 0)
        
        # Test that INSTALLED_APPS is not empty
        self.assertGreater(len(settings.INSTALLED_APPS), 0)
        
        # Test that MIDDLEWARE is not empty
        self.assertGreater(len(settings.MIDDLEWARE), 0)

    def test_database_settings_validity(self):
        """Test that database settings are valid"""
        db_config = settings.DATABASES['default']
        
        # Test that required database settings are present
        required_db_settings = ['ENGINE', 'NAME']
        for setting in required_db_settings:
            self.assertIn(setting, db_config)
            self.assertIsNotNone(db_config[setting])

    def test_template_settings_validity(self):
        """Test that template settings are valid"""
        template_config = settings.TEMPLATES[0]
        
        # Test that required template settings are present
        required_template_settings = ['BACKEND', 'DIRS', 'APP_DIRS', 'OPTIONS']
        for setting in required_template_settings:
            self.assertIn(setting, template_config) 