from http import HTTPStatus
from django.test import TestCase, Client


class TestAboutUrls(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_about_urls_guest(self):
        """Тестируем доступность url страниц
        'Об авторе' и 'Технологии'"""
        test_urls = [
            '/about/author/',
            '/about/tech/',
        ]
        for url in test_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
