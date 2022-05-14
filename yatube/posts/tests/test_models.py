from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.post = PostModelTest.post
        cls.field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        cls.field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к который будет относиться пост',
        }

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        for field, expected_value in self.field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name, expected_value
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        for field, expected_value in self.field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, expected_value
                )

    def test_models_have_current_objects_post(self):
        """Проверяем, что у моделей корректно работает __str__."""
        expected_object_name = self.post.text[:15]
        self.assertEqual(expected_object_name, str(self.post))
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
