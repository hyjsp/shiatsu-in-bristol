from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.core import mail


class CustomUserTests(TestCase):
    def test_create_user(self):
        User = get_user_model()
        user = User.objects.create_user(
            username="will", email="will@email.com", password="testpass123"
        )
        self.assertEqual(user.username, "will")
        self.assertEqual(user.email, "will@email.com")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        User = get_user_model()
        admin_user = User.objects.create_superuser(
            username="superadmin", email="superadmin@email.com", password="testpass123"
        )
        self.assertEqual(admin_user.username, "superadmin")
        self.assertEqual(admin_user.email, "superadmin@email.com")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)


class AccountsFlowTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username="testuser", email="testuser@email.com", password="testpass123"
        )

    def test_user_registration(self):
        response = self.client.post(reverse('account_signup'), {
            'email': 'newuser@email.com',
            'password1': 'newpass12345',
            'password2': 'newpass12345',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after signup
        self.assertTrue(self.User.objects.filter(email='newuser@email.com').exists())

    def test_login_logout(self):
        login = self.client.login(email="testuser@email.com", password="testpass123")
        self.assertTrue(login)
        response = self.client.get(reverse('account_logout'))
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_password_reset(self):
        response = self.client.post(reverse('account_reset_password'), {
            'email': 'testuser@email.com'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('testuser@email.com', mail.outbox[0].to)

    # Commented out until profile views are implemented
    # def test_profile_update(self):
    #     # Only if you have a profile update view/form
    #     self.client.login(email="testuser@email.com", password="testpass123")
    #     response = self.client.post(reverse('profile_update'), {
    #         'username': 'updateduser',
    #         'email': 'updated@email.com'
    #     })
    #     self.assertEqual(response.status_code, 302)
    #     self.user.refresh_from_db()
    #     self.assertEqual(self.user.username, 'updateduser')
    #     self.assertEqual(self.user.email, 'updated@email.com')

    # Commented out until profile views are implemented
    # def test_profile_permission(self):
    #     # Only users can access their own profile
    #     self.client.login(email="testuser@email.com", password="testpass123")
    #     other_user = self.User.objects.create_user(
    #         username="other", email="other@email.com", password="otherpass123"
    #     )
    #     response = self.client.get(reverse('profile_detail', kwargs={'pk': other_user.pk}))
    #     self.assertEqual(response.status_code, 403)  # Forbidden