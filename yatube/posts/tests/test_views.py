from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()


class PostPageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-slug',
            description='test-description',
        )
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPageTest.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html':
                reverse('posts:group_list', args=[self.group.slug]),
            'posts/profile.html':
                reverse('posts:profile', args=[self.user.username]),
            'posts/post_detail.html':
                reverse('posts:post_detail', args=[self.post.id]),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_paginator_context(self):
        """"Проверка контекста пагинатора index, group_list_, profile"""
        get_reverse = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[self.group.slug]),
            reverse('posts:profile', args=[self.user.username]),
        ]
        for page in get_reverse:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.text, 'test-text')
                self.assertEqual(first_object.author, PostPageTest.user)
                self.assertEqual(first_object.group, PostPageTest.group)

    def test_page_context_without_paginator(self):
        """"Проверка контекста group_list_, profile, post_detail"""
        get_reverse = [
            reverse('posts:group_list', args=[self.group.slug]),
            reverse('posts:profile', args=[self.user.username]),
            reverse('posts:post_detail', args=[self.post.id]),
        ]
        for page in get_reverse:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(
                    response.context.get('post').group.title,
                    'test-title'
                )
                self.assertEqual(
                    response.context.get('post').group.slug,
                    'test-slug'
                )
                self.assertEqual(
                    response.context.get('post').group.description,
                    'test-description'
                )
                self.assertEqual(
                    response.context.get('post').author.username,
                    'auth'
                )
                self.assertEqual(
                    response.context.get('post').text,
                    'test-text'
                )
                self.assertEqual(
                    response.context.get('post').author,
                    PostPageTest.user
                )
                self.assertEqual(
                    response.context.get('post').group,
                    PostPageTest.group
                )

    def test_create_post_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_correct_context(self):
        """Шаблон create_post(edit) сформирован с правильным контекстом."""
        """URL-адресс использует правильный шаблон"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=[self.post.id]))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=[self.post.id]))
        self.assertTemplateUsed(response, 'posts/create_post.html')


class TestPaginatorView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test-title',
            slug='test-slug',
            description='test-description',
        )
        cls.post = [Post.objects.bulk_create(
            Post(
                text=f'test-text {i}',
                group=cls.group,
                author=cls.user,
            ) for i in range(13)
        )]

    def setUp(self):
        self.guest = Client()

    def test_paginator_pages(self):
        first_page: int = 10
        second_page: int = 3
        paginator_page = {
            reverse('posts:index'): first_page,
            reverse('posts:index') + '?page=2': second_page,
            reverse('posts:group_list', args=[self.group.slug]): first_page,
            reverse('posts:group_list', args=[self.group.slug]) + '?page=2':
                second_page,
            reverse('posts:profile', args=[self.user.username]): first_page,
            reverse('posts:profile', args=[self.user.username]) + '?page=2':
                second_page,
        }
        for page, count_post in paginator_page.items():
            with self.subTest(count_post=count_post):
                response = self.guest.get(page)
                self.assertEqual(
                    len(response.context['page_obj']), count_post
                )


class FollowingTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.user = User.objects.create_user(username='user')

    def setUp(self):
        self.auth_author = Client()
        self.auth_author.force_login(user=self.author)
        self.auth_user = Client()
        self.auth_user.force_login(user=self.user)

    def test_user_following_author(self):
        """Проверка подписки на автора"""
        follow_count = Follow.objects.count()
        new_follower = Follow.objects.create(
            user=self.user,
            author=self.author,
        )
        self.auth_user.post(
            reverse('posts:profile_follow', args=[self.author]),
            data=new_follower,
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
