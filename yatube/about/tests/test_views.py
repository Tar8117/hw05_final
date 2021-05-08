from django.test import Client, TestCase
from django.urls import reverse


class TestAboutViews(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_about_views_correct_template(self):
        """Тестируем корректный показ шаблонов
        для страниц 'Об авторе' и 'Технологии'"""
        template_pages_names = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech')}
        for template, reverse_name in template_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
