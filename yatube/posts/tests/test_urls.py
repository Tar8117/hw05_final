from http import HTTPStatus

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from ..models import Group, Post

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Ragnar')
        cls.another_user = User.objects.create_user(username='Jhon')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Описание',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            group=cls.group,
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.another_user_client = Client()
        self.another_user_client.force_login(self.another_user)

    def test_urls_templates_guest_user(self):
        """Проверка соответствия шаблона
        при вызове страниц для неавторизованных"""
        url_templates_names = {
            '/': 'index.html',
            f'/group/{self.group.slug}/': 'group.html',
        }
        for url, template in url_templates_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_urls_templates_authorized_user(self):
        """Проверка соответствия шаблона
        при вызове страниц для авторизованных"""
        urls_templates_names = {
            '/new/': 'new.html',
            f'/{self.user.username}/{self.post.id}/edit/': 'new.html',
        }
        for url, template in urls_templates_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_new_post_url_guest_user(self):
        """Доступность страницы создания поста для неавторизованных"""
        response = self.guest_client.get('/new/')
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_post_edit_url_guest(self):
        """Доступность страницы редактирования поста для неавторизованных"""
        response = self.guest_client.get(f'/{self.user}/{self.post.id}/edit/')
        self.assertRedirects(
            response, f'/auth/login/?next=/{self.user}/{self.post.id}/edit/')

    def test_post_edit_url_authorised_not_author(self):
        """Доступность страницы редактирования поста для не автора поста"""
        response = self.another_user_client.get(
            f'/{self.user.username}/{self.post.id}/edit/')
        self.assertRedirects(
            response, f'/{self.user.username}/{self.post.id}/')

    def test_urls_guest_client_200(self):
        """Тест страниц 200 для неавторизованных"""
        test_urls = [
            '/',
            f'/group/{self.group.slug}/',
            f'/{self.user.username}/',
            f'/{self.user.username}/{self.post.id}/',
        ]
        for url in test_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_authorized_client_200(self):
        """Тест страниц 200 для авторизванных"""
        test_urls = [
            '/new/',
            f'/{self.user.username}/{self.post.id}/edit/',
        ]
        for url in test_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_404(self):
        """Доступность страницы 404"""
        response = self.guest_client.get('404/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
