from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus


class StaticURLTest(TestCase):
    def setUp(self):
        self.guest = Client()

    def test_status_url(self):
        """Проверка доступности адресов about"""
        status_url_names = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for address, status in status_url_names.items():
            with self.subTest(status=status):
                response = self.guest.get(address)
                self.assertEqual(response.status_code, status)

    def test_status_template(self):
        templates_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/'
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest.get(address)
                self.assertTemplateUsed(response, template)


class StaticViewsTest(TestCase):
    def setUp(self):
        self.guest = Client()

    def test_about_author_correct_name(self):
        response = self.guest.get(reverse('about:author'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_tech_correct_name(self):
        response = self.guest.get(reverse('about:tech'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_author_correct_template(self):
        response = self.guest.get(reverse('about:author'))
        self.assertTemplateUsed(response, 'about/author.html')

    def test_about_tech_correct_template(self):
        response = self.guest.get(reverse('about:tech'))
        self.assertTemplateUsed(response, 'about/tech.html')
