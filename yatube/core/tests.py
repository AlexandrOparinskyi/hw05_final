from django.test import TestCase, Client


class CoreURLTest(TestCase):
    def setUp(self):
        self.guest = Client()

    def test_404_error_used_correct_template(self):
        response = self.guest.get('/error/error/')
        self.assertTemplateUsed(response, 'core/404.html')
