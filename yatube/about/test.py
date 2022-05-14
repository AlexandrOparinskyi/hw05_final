from django.test import Client, TestCase

from http import HTTPStatus


class StaticURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.status_url_names = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        cls.templates_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/'
        }

    def setUp(self):
        self.guest = Client()

    def test_status_url(self):
        """Проверка доступности адресов about"""
        for address, status in self.status_url_names.items():
            with self.subTest(status=status):
                response = self.guest.get(address)
                self.assertEqual(response.status_code, status)

    def test_status_template(self):
        for template, address in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest.get(address)
                self.assertTemplateUsed(response, template)
