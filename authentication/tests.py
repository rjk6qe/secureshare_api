from django.test import Client
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.contrib.auth.models import User, Group

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from authentication.models import UserProfile
from report.models import Report, Document
from report.serializers import ReportSerializer

from Crypto.PublicKey import RSA
from base64 import b64decode
import random
import os

class UserTests(APITestCase):

	list_of_users = ['user1','user2','user3']
	list_of_passwords = ['password1','password2','user3']

	email = 'richard.github@gmail.com'

	user_data = {"username":list_of_users[0],"password":list_of_passwords[0],"email":"fake@fake.com"}


	register_url = '/api/v1/users/register/'
	login_url = '/api/v1/users/login/'
	logout_url = '/api/v1/users/logout/'
	report_list_url = '/api/v1/reports/'
	group_url = '/api/v1/users/groups/'

	serializer_class = ReportSerializer

	def generate_users_receive_tokens(self):
		size_of_list = len(self.list_of_users)
		token_list = []
		
		for i in range(0, size_of_list):
			user = User.objects.create(
				username=self.list_of_users[i],
				password=self.list_of_passwords[i]
				)
			UserProfile.objects.create(
				user=user
				)
			token = Token.objects.create(
				user=user
				)
			token_list.append(token.key)
		return token_list

	def test_register_user(self):
		response = self.client.post(self.register_url, self.user_data, format='json')

		self.assertEqual(
			response.status_code, 
			status.HTTP_201_CREATED,
			msg="Registration failed" + str(response.data)
			)

		self.assertEqual(
			User.objects.count(), 
			1,
			msg="Registration did not create a new User object"
			)

		self.assertEqual(
			User.objects.get(pk=1).username,
			self.user_data['username'],
			msg="Registration created a User object with an incorrect username"
			)

		response = self.client.post(self.register_url, self.user_data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_400_BAD_REQUEST,
			msg="Registration allowed the same username twice"
			)

		self.assertEqual(
			User.objects.count(),
			1,
			msg="Failed registration still created a user"
			)

	def test_login_user(self):

		user = User.objects.create(
			username=self.user_data['username'],
			)
		user.set_password(self.user_data['password'])
		user.save()

		response = self.client.post(self.login_url, self.user_data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Login failed"
			)
		try:
			self.assertEqual(
				Token.objects.get(user=user).key,
				response.data['key'],
				msg="Login returned the incorrect key"
				)
			self.assertEqual
		except ObjectDoesNotExist:
			self.fail(msg="Login failed because the key did not exist")

	def test_logout_user(self):

		user = User.objects.create(
			username=self.user_data['username']
			)
		user.set_password(self.user_data['password'])
		user.save()
		
		response = self.client.post(self.login_url, self.user_data, format='json')

		first_token = response.data['key']

		response = self.client.post(self.login_url, self.user_data, format='json')
		second_token = response.data['key']

		self.assertEqual(
			first_token,
			second_token,
			msg="Consecutive logins created new tokens"
			)

		self.client.credentials(HTTP_AUTHORIZATION="Token " + str(first_token))
		response = self.client.get(self.logout_url)

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Logout failed for logged in user"
			)

		self.assertEqual(
			Token.objects.filter(user=user).count(),
			0,
			msg="Token still exists for given user"
			)

		response = self.client.get(self.report_list_url)

		self.assertEqual(
			response.status_code,
			status.HTTP_401_UNAUTHORIZED,
			msg="Logged out user was allowed access with old token"
			)

		self.client.credentials()
		response = self.client.post(self.login_url, self.user_data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Could not log in with logged out user" + str(response.data)
			)

		third_token = response.data['key']

		self.assertNotEqual(
			third_token,
			first_token,
			msg="New token was not created on login"
			)

	def test_group_creation(self):
		token_list = self.generate_users_receive_tokens()
		user_one_token = token_list[0]
		user_two_token = token_list[1]
		user_three_token = token_list[2]

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])
		user_three = User.objects.get(username=self.list_of_users[2])

		group_data = {"name":"group 1", "users":[user_two.username,]}

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_one_token))
		response = self.client.post(self.group_url, group_data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_201_CREATED,
			msg="Group creation returned incorrect response code" + str(response.data)
			)

		self.assertEqual(
			Group.objects.count(),
			1,
			msg="Group object not created"
			)
		self.assertEqual(
			Group.objects.get().name,
			group_data['name'],
			msg="Group creation gave the wrong name"
			)

		group = Group.objects.get()
		
		self.assertEqual(
			group in user_one.groups.all(),
			True,
			msg="Group was not in creator's groups"
			)
		self.assertEqual(
			group in user_two.groups.all(),
			True,
			msg="Group was not in listed users' groups"
			)

	def test_group_modification(self):
		token_list = self.generate_users_receive_tokens()
		user_one_token = token_list[0]
		user_two_token = token_list[1]
		user_three_token = token_list[2]

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])
		user_three = User.objects.get(username=self.list_of_users[2])

		group_data = {"name":"group 1", "users":[user_two.username,]}

		group = Group.objects.create(
			name=group_data['name']
			)

		user_one.groups.add(group)
		user_two.groups.add(group)

		user_one.save()
		user_two.save()

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])		

		group_data['delete'] = True
		group_data['users'] = [user_two.username,]

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_one_token))
		response = self.client.patch(self.group_url, group_data, format='json')

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Group modification returned incorrect response code" + str(response.data)
			)
		
		self.assertEqual(
			group in user_one.groups.all(),
			True,
			msg="Group modification deleted incorrect user"
			)

		self.assertEqual(
			group in user_two.groups.all(),
			False,
			msg="Group modification did not delete user"
			)		

		group_data['delete'] = False

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_two_token))
		response = self.client.patch(self.group_url, group_data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_400_BAD_REQUEST,
			msg="Outside user was able to add self to group"
			)

		user_two.groups.add(group)
		user_two.save()

		user_profile = UserProfile.objects.get(user=user_three)
		user_profile.site_manager=True
		user_profile.save()

		group_data['delete'] = False

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_three_token))
		response = self.client.patch(self.group_url, group_data, format='json')		

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Site manager was not allowed to modify group" + str(response.data)
			)
