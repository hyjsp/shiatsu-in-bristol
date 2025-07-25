"""django_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
import sys

urlpatterns = [
    # Django admin
    path('nothingtoseehere/', admin.site.urls),
    # User Management
    path('accounts/', include('allauth.urls')),
    path('accounts/', include(('accounts.urls', 'account'), namespace='account')),
    # Products app should come before the root path
    path('bookings/', include('products.urls')),
    # Local
    path("", include('pages.urls')),
]

if settings.DEBUG and not any('test' in arg for arg in sys.argv):
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
