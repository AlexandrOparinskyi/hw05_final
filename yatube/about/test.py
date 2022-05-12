from django.test import Client, TestCase

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
