from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class PostFormTest(TestCase):
    def setUp(self):
        self.guest = Client()

    def test_create_new_user(self):
        """Проверка добавления нового пользователя в базу данных"""
        count_users = User.objects.count()
        new_user = {
            'first_name': 'Ivan',
            'last_name': 'Ivanov',
            'username': 'Ivanov',
            'email': 'test@ya.ru',
            'password1': 'BadPassword123',
            'password2': 'BadPassword123',
        }
        response = self.guest.post(
            reverse('users:signup'),
            data=new_user,
            fallow=True,
        )
        self.assertRedirects(response, reverse('posts:index'))
        self.assertEqual(User.objects.count(), count_users + 1)
