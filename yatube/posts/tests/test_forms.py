import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
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
            group=cls.group,
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_count = Post.objects.count()

    def test_post_create(self):
        """Форма заполняется"""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        new_post = {
            'text': 'test-text add',
            'group': '1',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=new_post,
            follow=True)
        self.assertEqual(Post.objects.count(), self.post_count + 1)
        self.assertRedirects(
            response, reverse('posts:profile', args=[self.user.username]))
        self.assertTrue(
            Post.objects.filter(
                text='test-text add',
                group='1',
                image='posts/small.gif'
            ).exists()
        )

    def test_guest_create_post(self):
        new_post = {
            'text': 'test_guest',
            'group': '1',
        }
        response = self.guest.post(
            reverse('posts:post_create'),
            data=new_post,
            fallow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Post.objects.count(), self.post_count)

    def test_is_not_valid_form_post(self):
        new_post = {
            'text': '',
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=new_post,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), self.post_count)

    def test_post_edit(self):
        edit_post = {
            'text': 'test-text add',
            'group': '1',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[self.post.id]),
            data=edit_post,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=[self.post.id]))
        self.assertTrue(
            Post.objects.filter(
                text='test-text add',
                group='1',
            ).exists()
        )


class PostsCommentsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.user,
        )
        cls.comment = Comment.objects.create(
            text='test-text'
        )

    def setUp(self):
        self.guest = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_guest_add_posts_comment(self):
        """Проверка создания комментария гостем"""
        comment_count = Comment.objects.count()
        new_comment = {
            'text': 'text-test',
        }
        self.guest.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=new_comment,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comment_count)

    def test_add_posts_comment(self):
        """Проверка добавления комментария к посту"""
        comment_count = Comment.objects.count()
        new_comment = {
            'text': 'text-test',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=new_comment,
            follow=True,
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)


class CachePostsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_add_post_in_cache(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.post.delete()
        self.assertIn(self.post, response.content)
        cache.clear()
        self.assertNotIn(self.post, response.content)


