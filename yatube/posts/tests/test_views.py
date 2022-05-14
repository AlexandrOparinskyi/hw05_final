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
        cls.templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html':
                reverse('posts:group_list', args=[cls.group.slug]),
            'posts/profile.html':
                reverse('posts:profile', args=[cls.user.username]),
            'posts/post_detail.html':
                reverse('posts:post_detail', args=[cls.post.id]),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        cls.get_reverse_with_paginator = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[cls.group.slug]),
            reverse('posts:profile', args=[cls.user.username]),
        ]
        cls.get_reverse_without_paginator = [
            reverse('posts:group_list', args=[cls.group.slug]),
            reverse('posts:profile', args=[cls.user.username]),
            reverse('posts:post_detail', args=[cls.post.id]),
        ]
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPageTest.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_paginator_context(self):
        """"Проверка контекста пагинатора index, group_list_, profile"""
        for page in self.get_reverse_with_paginator:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.text, 'test-text')
                self.assertEqual(first_object.author, PostPageTest.user)
                self.assertEqual(first_object.group, PostPageTest.group)

    def test_page_context_without_paginator(self):
        """"Проверка контекста group_list_, profile, post_detail"""
        for page in self.get_reverse_without_paginator:
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
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_correct_context(self):
        """Шаблон create_post(edit) сформирован с правильным контекстом.
        URL-адресс использует правильный шаблон
        """
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=[self.post.id]))
        for value, expected in self.form_fields.items():
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
        Post.objects.bulk_create(
            Post(
                text=f'test-text {i}',
                group=cls.group,
                author=cls.user,
            ) for i in range(13)
        )
        first_page: int = 10
        second_page: int = 3
        cls.paginator_page = {
            reverse('posts:index'): first_page,
            reverse('posts:index') + '?page=2': second_page,
            reverse('posts:group_list', args=[cls.group.slug]): first_page,
            reverse('posts:group_list', args=[cls.group.slug]) + '?page=2':
                second_page,
            reverse('posts:profile', args=[cls.user.username]): first_page,
            reverse('posts:profile', args=[cls.user.username]) + '?page=2':
                second_page,
        }

    def setUp(self):
        self.guest = Client()

    def test_paginator_pages(self):
        for page, count_post in self.paginator_page.items():
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
        cls.user_1 = User.objects.create_user(username='_1')
        cls.bad_user = User.objects.create_user(username='bad_user')
        cls.new_follower = {
            'user': cls.author,
            'author': cls.user,
        }
        cls.follow = Follow.objects.create(
            user=cls.user_1,
            author=cls.author,
        )

    def setUp(self):
        self.auth_author = Client()
        self.auth_author.force_login(user=self.author)
        self.auth_user_1 = Client()
        self.auth_user_1.force_login(user=self.user_1)
        self.auth_user = Client()
        self.auth_user.force_login(user=self.user)
        self.auth_bad_user = Client()
        self.auth_bad_user.force_login(user=self.bad_user)
        self.follow_count = Follow.objects.count()
        self.post_count = Post.objects.count()

    def test_user_following_author(self):
        """Проверка подписки автора"""
        self.auth_user.post(
            reverse('posts:profile_follow', args=[self.author]),
            data=self.new_follower,
            follow=True,
        )
        self.assertEqual(Follow.objects.count(), self.follow_count + 1)

    def test_user_unfollowing_author(self):
        """Проверка отписки от автора"""
        self.auth_user_1.post(
            reverse('posts:profile_unfollow', args=[self.author]),
            cleaned_data=self.new_follower,
            follow=True,
        )
        self.assertEqual(Follow.objects.count(), self.follow_count - 1)

    def test_author_follow_on_author(self):
        """Автор не может подписаться на себя самого"""
        self.auth_author.post(
            reverse('posts:profile_follow', args=[self.author]),
            data={
                'user': self.author,
                'author': self.author,
            },
        )
        self.assertEqual(Follow.objects.count(), self.follow_count)

    def test_new_posts_in_follow(self):
        """Появление новой записи у подписанных пользователей"""
        self.auth_user.post(
            reverse('posts:profile_follow', args=[self.author]),
            data=self.new_follower,
            follow=True,
        )
        response = self.auth_user.get(
            reverse('posts:follow_index')
        )
        follower_post_count = len(response.context['page_obj'].object_list)
        self.auth_author.post(
            reverse('posts:post_create'),
            data={'text': 'new_text'},
            follow=True,
        )
        new_response = self.auth_user.get(
            reverse('posts:follow_index')
        )
        follower_new_post_count = len(
            new_response.context['page_obj'].object_list
        )
        self.assertEqual(self.post_count, follower_post_count)
        self.assertEqual(self.post_count + 1, follower_new_post_count)

    def test_non_post_in_unfollow(self):
        """Отсутствие новой записи у неподписанного пользователя"""
        self.auth_user.post(
            reverse('posts:profile_follow', args=[self.author]),
            data=self.new_follower,
            follow=True,
        )
        response = self.auth_bad_user.get(
            reverse('posts:follow_index')
        )
        unfollower_post_count = len(response.context['page_obj'].object_list)
        self.auth_author.post(
            reverse('posts:post_create'),
            data={'text': 'new_text'},
            follow=True,
        )
        new_response = self.auth_bad_user.get(
            reverse('posts:follow_index')
        )
        unfollower_new_post_count = len(
            new_response.context['page_obj'].object_list
        )
        self.assertEqual(self.post_count, unfollower_post_count)
        self.assertEqual(self.post_count, unfollower_new_post_count)
