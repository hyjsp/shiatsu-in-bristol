from django.shortcuts import render

from django.views.generic import TemplateView


class HomePageView(TemplateView):
    template_name = "home.html"

class ShiatsuMassageView(TemplateView):
    template_name = "shiatsu_massage.html"

class LocationView(TemplateView):
    template_name = 'location.html'

class ShiatsuFeesView(TemplateView):
    template_name = 'shiatsu_fees.html'

class ShiatsuHistoryView(TemplateView):
    template_name = 'shiatsu_history.html'

class MatthewFerinView(TemplateView):
    template_name = 'matthew_ferin.html'

class LinksView(TemplateView):
    template_name = 'links.html'
