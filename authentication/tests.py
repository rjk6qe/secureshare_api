from django.test import Client
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from django.contrib.auth.models import User
from authentication.models import UserProfile
from report.models import Report, Document
from report.serializers import ReportSerializer

import random




class UserTests(APITestCase):

	username = 'test_user'
	password = 'test_password'

	list_of_users = ['user1','user2','user3','user4','user5']
	list_of_passwords = ['password1',' password2', 'password3', 'password4', 'password5']

	register_url = '/api/v1/register/'
	login_url = '/api/v1/login/'

	def test_register_user(self):
		size_of_list = len(self.list_of_users)
		for i in range(0,size_of_list):
			data = {"username": self.list_of_users[i], "password" : self.list_of_passwords[i]}
			response = self.client.post(self.register_url, data, format='json')
			response_data = response.data

			self.assertEqual(
				response.status_code, 
				status.HTTP_201_CREATED, 
				msg="Incorrect status code" + str(response.data)
				)
			self.assertEqual(
				User.objects.count(), 
				i+1,
				msg="Incorrect number of users"
				)
			self.assertEqual(
				User.objects.get(pk=i+1).username,
				self.list_of_users[i],
				msg="Incorrect username"
				)
			self.assertEqual(
				User.objects.get(pk=i+1).password,
				response_data['password'],
				msg="Incorrect hash object"
				)
			try:
				user_profile = UserProfile.objects.get(user=User.objects.get(pk=i+1))
				self.assertEqual(
					user_profile.site_manager,
					False,
					msg="UserProfile incorrectly gives sitemanager status"
					)
			except ObjectDoesNotExist:
				self.fail("UserProfile objects not created")

	def test_login_user(self):
		data = {'username' : self.username, 'password' : self.password}

		register_response = self.client.post(self.register_url, data, format='json')
		
		user = User.objects.get(username = self.username)
		token = Token.objects.get(user=user)

		expected_response = {'token': token.key}

		response = self.client.post(self.login_url, data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Incorrect status code"
			)
		self.assertEqual(
			response.data,
			expected_response,
			msg="Incorrect token"
			)