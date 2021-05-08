from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models import Group, Post

User = get_user_model()


class ModelsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Ragnar')
        cls.group = Group.objects.create(
            title='Название группы',
            slug='test',
            description='текст'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='текст тестовый',
            group=cls.group
        )

    def test_post_have_correct_object_name(self):
        value = str(self.post)
        expected = self.post.text[:15]
        self.assertEqual(
            value,
            expected,
            'Метод __str__ модели Post работает не правильно.'
        )

    def test_group_have_correct_object_name(self):
        value = str(self.group)
        expected = self.group.title
        self.assertEqual(
            value,
            expected,
            'Метод __str__ модели Group работает не правильно.'
        )
