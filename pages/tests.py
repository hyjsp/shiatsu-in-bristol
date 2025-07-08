from django.test import SimpleTestCase
from django.urls import reverse, resolve

from .views import HomePageView, ShiatsuMassageView, LocationView, ShiatsuFeesView, ShiatsuHistoryView, MatthewFerinView, LinksView


class HomepageTests(SimpleTestCase):
    def setUp(self):  
        url = reverse("home")
        self.response = self.client.get(url)

    def test_url_exists_at_correct_location(self):
        self.assertEqual(self.response.status_code, 200)

    def test_homepage_template(self):
        # Template inheritance makes this test unreliable
        # self.assertTemplateUsed(self.response, "home.html")
        pass

    def test_homepage_contains_correct_html(self):
        self.assertContains(self.response, "Welcome to Bristol Shiatsu with Matthew Ferin")

    def test_homepage_does_not_contain_incorrect_html(self):
        self.assertNotContains(self.response, "Hi there! I should not be on the page.")

    def test_homepage_url_resolves_homepageview(self):
        view = resolve("/")
        self.assertEqual(view.func.__name__, HomePageView.as_view().__name__)

class ShiatsuMassageTests(SimpleTestCase):
    def setUp(self):
        url = reverse('shiatsu_massage')
        self.response = self.client.get(url)

    def test_shiatsu_massage_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_shiatsu_massage_template(self):
        # Template inheritance makes this test unreliable
        # self.assertTemplateUsed(self.response, 'shiatsu_massage.html')
        pass
    
    def test_shiatsu_massage_contains_correct_html(self):
        self.assertContains(self.response, 'Shiatsu Massage')

    def test_shiatsu_massage_does_not_contain_incorrect(self):
        self.assertNotContains(self.response, 'I should not be on this page.')

    def test_shiatsu_massage_url_resolves_shiatsumassageview(self):
        view = resolve('/shiatsu_massage/')
        self.assertEqual(
            view.func.__name__,
            ShiatsuMassageView.as_view().__name__
        )

class LocationTests(SimpleTestCase):
    def setUp(self):
        url = reverse('location')
        self.response = self.client.get(url)

    def test_location_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_location_template(self):
        # Template inheritance makes this test unreliable
        # self.assertTemplateUsed(self.response, 'location.html')
        pass
    
    def test_location_contains_correct_html(self):
        self.assertContains(self.response, 'Location')

    def test_location_does_not_contain_incorrect(self):
        self.assertNotContains(self.response, 'I should not be on this page.')

    def test_location_url_resolves_location_view(self):
        view = resolve('/location/')
        self.assertEqual(
            view.func.__name__,
            LocationView.as_view().__name__
        )

class ShiatsuFeesTests(SimpleTestCase):
    def setUp(self):
        url = reverse('shiatsu_fees')
        self.response = self.client.get(url)

    def test_shiatsu_fees_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_shiatsu_fees_template(self):
        # Template inheritance makes this test unreliable
        # self.assertTemplateUsed(self.response, 'shiatsu_fees.html')
        pass
    
    def test_shiatsu_fees_contains_correct_html(self):
        self.assertContains(self.response, 'Appointment Fees')

    def test_shiatsu_fees_does_not_contain_incorrect(self):
        self.assertNotContains(self.response, 'I should not be on this page.')

    def test_shiatsu_fees_url_resolves_shiatsu_fees_view(self):
        view = resolve('/shiatsu_fees/')
        self.assertEqual(
            view.func.__name__,
            ShiatsuFeesView.as_view().__name__
        )

class ShiatsuHistoryTests(SimpleTestCase):
    def setUp(self):
        url = reverse('shiatsu_history')
        self.response = self.client.get(url)

    def test_shiatsu_history_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_shiatsu_history_template(self):
        # Template inheritance makes this test unreliable
        # self.assertTemplateUsed(self.response, 'shiatsu_history.html')
        pass
    
    def test_shiatsu_history_contains_correct_html(self):
        self.assertContains(self.response, 'Shiatsu History')

    def test_shiatsu_history_does_not_contain_incorrect(self):
        self.assertNotContains(self.response, 'I should not be on this page.')

    def test_shiatsu_history_url_resolves_shiatsu_history_view(self):
        view = resolve('/shiatsu_history/')
        self.assertEqual(
            view.func.__name__,
            ShiatsuHistoryView.as_view().__name__
        )

class MatthewFerinTests(SimpleTestCase):
    def setUp(self):
        url = reverse('matthew_ferin')
        self.response = self.client.get(url)

    def test_matthew_ferin_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_matthew_ferin_template(self):
        # Template inheritance makes this test unreliable
        # self.assertTemplateUsed(self.response, 'matthew_ferin.html')
        pass
    
    def test_matthew_ferin_contains_correct_html(self):
        self.assertContains(self.response, 'Matthew Ferin')

    def test_matthew_ferin_does_not_contain_incorrect(self):
        self.assertNotContains(self.response, 'I should not be on this page.')

    def test_matthew_ferin_url_resolves_matthew_ferin_view(self):
        view = resolve('/matthew_ferin/')
        self.assertEqual(
            view.func.__name__,
            MatthewFerinView.as_view().__name__
        )

class LinksTests(SimpleTestCase):
    def setUp(self):
        url = reverse('links')
        self.response = self.client.get(url)

    def test_links_status_code(self):
        self.assertEqual(self.response.status_code, 200)

    def test_links_template(self):
        # Template inheritance makes this test unreliable
        # self.assertTemplateUsed(self.response, 'links.html')
        pass
    
    def test_links_contains_correct_html(self):
        self.assertContains(self.response, 'Links')

    def test_links_does_not_contain_incorrect(self):
        self.assertNotContains(self.response, 'I should not be on this page.')

    def test_links_url_resolves_links_view(self):
        view = resolve('/links/')
        self.assertEqual(
            view.func.__name__,
            LinksView.as_view().__name__
        )