import shutil
import tempfile

from http import HTTPStatus
from django import forms
from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import TestCase, Client
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

from ..forms import PostForm
from ..models import Follow, Group, Post

User = get_user_model()


class ViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Ragnar')
        cls.group = Group.objects.create(
            title='Название',
            slug='test-1',
            description='Текст')
        cls.post = Post.objects.create(
            author=cls.user,
            text='текст',
            group=cls.group)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client2 = User.objects.create_user(username='user2')
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.guest_client2)
        self.guest_client3 = User.objects.create_user(username='user3')
        self.authorized_client3 = Client()
        self.authorized_client3.force_login(self.guest_client3)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    def test_pages_uses_correct_template(self):
        """Проверяем, что URL-адрес использует правильный шаблон"""
        templates_pages_names = {
            'index.html': reverse('index'),
            'group.html': reverse('group_posts', args=[self.group.slug]),
            'new.html': reverse('new_post'),
            'follow.html': reverse('follow_index'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_correct_context(self):
        """Проверяем, что шаблон index сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse('index'))
        self.assertIn('page', response.context)
        post = response.context.get('page')[0]
        self.assertEqual(post.text, ViewsTests.post.text)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)

    def test_group_correct_context(self):
        """Проверяем, что шаблон group сформирован с правильным контекстом"""
        response = self.guest_client.get(reverse('group_posts',
                                                 args=['test-1']))
        self.assertIn('page', response.context)
        post_object = response.context['page'][0]
        post_author_0 = post_object.author
        post_pub_date_0 = post_object.pub_date
        post_text_0 = post_object.text
        post_object_group = response.context['group']
        group_title = post_object_group.title
        group_description = post_object_group.description
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_pub_date_0, self.post.pub_date)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(group_title, self.group.title)
        self.assertEqual(group_description, self.group.description)

    def test_post_correct_context(self):
        """Проверяем, что шаблон post сформирован с правильным контекстом"""
        response = self.guest_client.get(
            reverse('post', args=[self.user.username, self.post.id])
        )
        post = response.context['post']
        self.assertEqual(post.author, self.user)
        self.assertEqual(post, self.post)

    def test_new_post_form(self):
        """Проверка страницы редактирования поста  на шаблон"""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(response.context['form'], PostForm)

    def test_post_edit_form(self):
        fields_list = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        response = self.authorized_client.get(
            reverse('post_edit', args=[self.user.username, self.post.id]))

        for value, expected in fields_list.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertEqual(response.context['post'].text, self.post.text)

    def test_post_edit_correct_context(self):
        """Проверяем, что шаблон post_edit
        сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('post_edit', args=[self.user.username, self.post.id])
        )
        self.assertIn('form', response.context)
        self.assertEqual(response.context['post'], self.post)

    def test_profile_correct_context(self):
        """Проверяем, что шаблон profile
        сформирован с правильными контекстом"""
        response = self.guest_client.get(
            reverse('profile', kwargs={'username': self.user.username}))
        post_text_0 = response.context.get('page')[0].text
        post_author_0 = response.context.get('page')[0].author
        post_group_0 = response.context.get('page')[0].group
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.user)
        self.assertEqual(post_group_0, self.group)

    def test_index_create_new_post(self):
        """Новый пост появляется на странице index"""
        response = self.authorized_client.get(reverse('index'))
        post_object = response.context['page'][0]
        post_text_index = post_object
        last_post = Post.objects.order_by('-pub_date')[0:1]
        self.assertEqual(post_text_index, last_post.get())

    def test_new_post_group_identification(self):
        """Новый пост  не  появляетя не в своей группе"""
        group = Group.objects.create(
            title='Название2',
            slug='test-2',
            description='Текст2')
        response = self.guest_client.get(
            reverse('group_posts', args=[group.slug]))
        post_count = len(response.context['page'])
        self.assertEqual(post_count, 0)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_cache(self):
        """Проверка работы кэша"""
        response_1 = self.guest_client.get(reverse('index'))
        Post.objects.create(text='test2', author=self.user)
        response_2 = self.guest_client.get(reverse('index'))
        cache.clear()
        response_3 = self.guest_client.get(reverse('index'))
        self.assertEqual(response_1.content, response_2.content,
                         'Кэширование не работает')
        self.assertNotEqual(response_2.content, response_3.content,
                            'Кэш не очистился')

    def test_auth_user_comment(self):
        """Проверка возможности авторизованного пользователя комментировать"""
        self.url_post = reverse('post', args=[self.user, self.post.id])
        self.url_comment = reverse('add_comment',
                                   args=[self.user, self.post.id]
                                   )

        self.authorized_client.post(self.url_comment, {'text': 'comment'})
        response = self.authorized_client.get(self.url_post)
        self.assertContains(response, 'comment')

    def test_index_image(self):
        Post.objects.create(
            text='test',
            author=self.user,
            group=self.group,
            image=self.uploaded
        )
        response = self.authorized_client.get(reverse('index'))
        posts = response.context.get('page').object_list
        self.assertListEqual(list(posts), list(Post.objects.all()[:10]))

    def test_group_image(self):
        Post.objects.create(
            text='test',
            author=self.user,
            group=self.group,
            image=self.uploaded)
        response = self.authorized_client.get(reverse('group_posts',
                                                      kwargs={'slug': 'test-1'}))
        posts = response.context.get('page').object_list
        self.assertListEqual(list(posts),
                             list(Post.objects.filter(author=self.user.id)))

    def test_profile_image(self):
        Post.objects.create(
            text='test',
            author=self.user,
            image=self.uploaded)
        response = self.authorized_client.get(
            reverse('profile', kwargs={'username': self.user}))

        posts = response.context.get('page').object_list
        self.assertListEqual(
            list(posts), list(Post.objects.filter(author=self.user.id)))

    def test_post_image(self):
        post = Post.objects.create(
            text='This is a test',
            author=self.user,
            group=self.group,
            image=self.uploaded
        )
        response = self.authorized_client.get(
            reverse(
                'post',
                kwargs={
                    'username': self.user,
                    'post_id': post.pk
                }
            )
        )
        post_context = response.context['post']
        self.assertEqual(post_context.text, post.text)
        self.assertEqual(post_context.author, self.user)
        self.assertEqual(post_context.group, self.group)
        self.assertEqual(post_context.image, post.image)

    def test_follow_index(self):
        Post.objects.create(
            text='post',
            author=self.guest_client2
        )
        Follow.objects.create(user=self.guest_client2, author=self.user)
        response = self.authorized_client2.get(reverse('follow_index'))
        posts = response.context.get('page').object_list
        self.assertListEqual(
            list(posts),
            list(Post.objects.filter(author=self.user.id)[:10])
        )

    def test_follow_index_not_behind_posts(self):
        Post.objects.create(
            text='post',
            author=self.guest_client2
        )
        Follow.objects.create(user=self.guest_client2, author=self.user)
        response_2 = self.authorized_client3.get(reverse('follow_index'))
        posts_2 = response_2.context.get('page').object_list
        self.assertListEqual(
            list(posts_2),
            list(Post.objects.filter(author=self.user.id)[2:])
        )

    def test_follow(self):
        count_follow = Follow.objects.count()
        self.authorized_client.get(reverse('profile_follow',
                                   kwargs={'username': 'user2'}))
        count_following = Follow.objects.all().count()
        self.assertEqual(count_following, count_follow + 1)

    def test_unfollow(self):
        Follow.objects.create(user=self.user, author=self.guest_client2)
        count_follow = Follow.objects.count()
        self.authorized_client.get(reverse('profile_unfollow',
                                   kwargs={'username': 'user2'}))
        count_following = Follow.objects.all().count()
        self.assertEqual(count_following, count_follow - 1)


class PaginatorViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('Ragnar')

        cls.group = Group.objects.create(
            title='Название',
            slug='test-1',
            description='Текст')
        for i in range(13):
            Post.objects.create(
                text=f'тестовый текст{i}',
                author=cls.user,
                group=cls.group)

    def setUp(self):
        self.guest_client = Client()

    def test_paginator_first_page(self):
        """Проверяем корректность показа постов
        на первой странице пагинатора"""
        response = self.guest_client.get(reverse('index'))
        self.assertEqual(
            len(response.context.get('page').object_list), 10)

    def test_paginator_second_page(self):
        """Проверяем корректность показа постов
        на второй странице пагинатора"""
        response = self.guest_client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)
