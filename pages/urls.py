from django.urls import path

from .views import HomePageView, ShiatsuMassageView, LocationView, ShiatsuFeesView, ShiatsuHistoryView, MatthewFerinView, LinksView

urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path('shiatsu_massage/', ShiatsuMassageView.as_view(), name='shiatsu_massage'),
    path('location/', LocationView.as_view(), name='location'),
    path('shiatsu_fees/', ShiatsuFeesView.as_view(), name='shiatsu_fees'),
    path('shiatsu_history/', ShiatsuHistoryView.as_view(), name='shiatsu_history'),
    path('matthew_ferin/', MatthewFerinView.as_view(), name='matthew_ferin'),
    path('links/', LinksView.as_view(), name='links'),
]