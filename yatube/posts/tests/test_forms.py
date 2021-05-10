import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from ..models import Group, Post, User

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class TestPostCreateForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Ragnar')
        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test-1',
            description='Описание'
        )
        cls.post = Post.objects.create(
            text='Текст',
            author=cls.user,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_new_post(self):
        """Тестируем создание нового поста"""
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
            content_type='image/gif')

        post_count = Post.objects.count()
        text = 'Текст2'
        form_data = {
            'text': text,
            'group': self.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data, follow=True
        )
        post = Post.objects.first()
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post.image, f'posts/{uploaded.name}')

    def test_edit_post(self):
        """Тестируем редактирование поста"""
        form_data = {
            'text': 'Текст2',
            'group': self.group.id}

        response = self.authorized_client.post(
            reverse('post_edit', args=[self.user, 1]),
            data=form_data,
            follow=True)
        self.assertRedirects(response,
                             reverse('post', args=[self.user, self.post.id]))
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(response.status_code, HTTPStatus.OK,
                         'Страница не отвечает')
        self.assertEqual(
            Post.objects.first().text,
            form_data['text'],
            'Пост не изменился!')
