from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class UserPageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_guest_pages_uses_correct_template(self):
        """Гостевой URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'users/login.html': reverse('users:login'),
            'users/password_reset_form.html': reverse('users:password_reset'),
            'users/password_reset_done.html':
                reverse('users:password_reset_done'),
            'users/signup.html': reverse('users:signup'),
            'users/password_reset_complete.html':
                reverse('password_reset_complete'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_authorized_pages_uses_correct_template(self):
        """Пользовательский URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'users/password_change_form.html':
                reverse('users:password_change'),
            'users/password_change_done.html':
                reverse('users:password_change_done'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_signup_post_correct_form_context(self):
        """Шаблон signup сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('users:signup'))
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
