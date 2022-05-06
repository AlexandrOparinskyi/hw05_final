from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_ap = User.objects.create(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user_ap,
            group=cls.group,
        )
        cls.status_url_names_guest = {
            '/': HTTPStatus.OK,
            '/group/test-slug/': HTTPStatus.OK,
            '/posts/1/': HTTPStatus.OK,
            '/profile/auth/': HTTPStatus.OK,
            '/unknown_page/': HTTPStatus.NOT_FOUND,
        }
        cls.status_url_names_auth = {
            '/posts/1/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
            '/follow/': HTTPStatus.OK,
            '/profile/auth/': HTTPStatus.OK,
            '/unknown_page/': HTTPStatus.NOT_FOUND,
        }
        cls.templates_url_names_guest = {
            'posts/index.html': '/',
            'posts/group_list.html': '/group/test-slug/',
            'posts/post_detail.html': '/posts/1/',
            'posts/profile.html': '/profile/auth/',
        }
        cls.templates_url_names_auth = {
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/profile/auth/': 'posts/profile.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.user_nap = User.objects.create_user(username='HasNoName')
        self.authorized_client_ap = Client()
        self.authorized_client_nap = Client()
        self.authorized_client_ap.force_login(PostURLTests.user_ap)
        self.authorized_client_nap.force_login(self.user_nap)

    def test_guest_client_status(self):
        """Проверка доступности адресов неавторизованных пользователей."""
        for address, status in self.status_url_names_guest.items():
            with self.subTest(status=status):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status)

    def test_authorized_client_status(self):
        """Проверка доступности адресов авторизованных пользователей."""
        for address, status in self.status_url_names_auth.items():
            with self.subTest(status=status):
                response = self.authorized_client_ap.get(address)
                self.assertEqual(response.status_code, status)

    def test_guest_client_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, address in self.templates_url_names_guest.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_authorized_client_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.templates_url_names_auth.items():
            with self.subTest(address=address):
                response = self.authorized_client_ap.get(address)
                self.assertTemplateUsed(response, template)

    def test_edit_another_users_url(self):
        """Проверка перенаправления со странички редактирования."""
        response = self.authorized_client_nap.get('/posts/1/edit/')
        self.assertRedirects(response, '/posts/1/')
