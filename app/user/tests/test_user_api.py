from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

import logging

logger = logging.getLogger(__name__)

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    """Helper function to create new user"""
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
            'name': 'test user'
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password', res.data)

    def test_duplicate_user_fails(self):
        """Test that creating a new user with the same email fails"""
        payload = {
            'email': 'test@gmail.com',
            'password': 'testpass',
            'name': 'test user'
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test that the password is more than 5 characters long"""
        payload = {
            'email': 'testpassword@gmail.com',
            'password': '12345',
            'name': 'test user'
        }

        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(
            email=payload['email']
        ).exists()
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test that a token is created for the user"""
        payload = {
            'email': 'test@gmail.com',
            'password': 'thisisatest'
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Test that the token is not created if invalid credentials are
           given"""
        create_user(email='test@gmail.com', password='testpassword')
        res = self.client.post(TOKEN_URL, {
            'email': 'test@gmail.com',
            'password': 'thewrongpassword'
        })

        self.assertNotIn('token', res.data)
        self.assertTrue(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Test that a token cannot be created if user does not exist"""
        res = self.client.post(TOKEN_URL, {
            'email': 'newuser@gmail.com',
            'password': 'newuserpassword'
        })

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creat_token_missing_password(self):
        """Test that a token is not created if password in missing"""
        create_user(email='test@gmail.com', password='testpass')
        res = self.client.post(TOKEN_URL, {
            'email': 'test@gmail.com'
        })

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
