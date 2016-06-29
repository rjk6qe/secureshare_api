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

	username = 'test_user'
	password = 'test_password'

	list_of_users = ['user1','user2']
	list_of_passwords = ['password1','password2']
	email = 'richard.github@gmail.com'

	user_data = {"username":list_of_users[0],"password":list_of_passwords[0],"email":"fake@fake.com","testing":'True'}

	register_url = '/api/v1/users/register/'
	login_url = '/api/v1/users/login/'
	logout_url = '/api/v1/users/logout/'
	report_list_url = '/api/v1/reports/'
	group_url = '/api/v1/users/groups/'
	generate_url = '/api/v1/encrypt/generate/'

	serializer_class = ReportSerializer

	def generate_users_receive_tokens(self):
		size_of_list = len(self.list_of_users)
		token_list = []
		
		for i in range(0, size_of_list):
			self.user_data['username'] = self.list_of_users[i]
			self.user_data['password'] = self.list_of_passwords[i]
			if i == 1:
				self.user_data['email'] = self.email
			self.client.post(self.register_url, self.user_data, format='json')
			self.assertEqual(
				User.objects.count(),
				i+1,
				msg="Users not created"
			)
			response = self.client.post(self.login_url, self.user_data, format='json')
			
			self.assertEqual(
				response.status_code,
				status.HTTP_200_OK,
				msg="invalid user"
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

			token_list.append(response.data['token'])
			self.user_data['email'] = 'fake@fake.com'
		return token_list

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

	def test_login_user(self):
		data = {'username' : self.username, 'password' : self.password}

		register_response = self.client.post(self.register_url, data, format='json')
		
		user = User.objects.get(username = self.username)

		response = self.client.post(self.login_url, data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Incorrect status code"
			)
		try:
			self.assertEqual(
				Token.objects.get(user=user).key,
				response.data['token'],
				msg="Incorrect token returned"
				)
		except ObjectDoesNotExist:
			self.fail(msg="Token does not exist")



	def test_logout_user(self):
		data = {'username' : self.username, 'password' : self.password}

		self.client.post(self.register_url, data, format='json')
		response = self.client.post(self.login_url, data, format='json')

		first_token = response.data['token']

		user = Token.objects.get(key=first_token).user

		self.client.credentials(HTTP_AUTHORIZATION= 'Token ' + str(first_token))
		response = self.client.get(self.report_list_url)

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="First token did not work"
			)

		response = self.client.post(self.login_url, data, format='json')

		second_token = response.data['token']

		self.assertEqual(
			first_token,
			second_token,
			msg="New token created for multiple logins"
			)

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
			msg="Old token still allowed access"
			)

		self.client.credentials()
		response = self.client.post(self.login_url, data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Could not log in with logged out user" + str(response.data)
			)

		third_token = response.data['token']

		self.assertNotEqual(
			third_token,
			first_token,
			msg="New token was not created on login"
			)


	def test_groups(self):
		token_list = self.generate_users_receive_tokens()
		user_one_token = token_list[0]

		user_two_token = token_list[1]
		user_two_username = self.list_of_users[1]

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_one_token))
		group_data = {}
		group_data["group_name"]= "group_one" 
		group_data["users"] = [user_two_username,]

		response = self.client.post(self.group_url, group_data, format='json')
		self.assertEqual(
			response.status_code,
			status.HTTP_201_CREATED,
			msg="Incorrect response code for group creation" + str(response.data)
			)
		self.assertEqual(
			Group.objects.count(),
			1,
			msg="Group not created"
			)
		group = Group.objects.get()
		self.assertEqual(
			group in Token.objects.get(key=user_one_token).user.groups.all(),
			True,
			msg="Group not in creator's groups"
			)
		self.assertEqual(
			group in Token.objects.get(key=user_two_token).user.groups.all(),
			True,
			msg="Group not in listed users' groups"
			)

		group_data['delete'] = True
		response = self.client.patch(self.group_url, group_data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Incorrect response code for group modification" + str(response.data)
			)
		self.assertEqual(
			group in Token.objects.get(key=user_one_token).user.groups.all(),
			True,
			msg="Group modification deleted wrong user"
			)
		self.assertEqual(
			group in Token.objects.get(key=user_two_token).user.groups.all(),
			False,
			msg="Group modification did not delete user"
			)		

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_two_token))
		group_data['delete'] = False
		response = self.client.patch(self.group_url, group_data, format='json')

		self.assertEqual(
			status.HTTP_400_BAD_REQUEST,
			response.status_code,
			msg="Outside user was able to add self to group"
			)






	# def test_generate_post_key(self):
	# 	token_list = self.generate_users_receive_tokens()

	# 	self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_list[3])
	# 	user = Token.objects.get(key=token_list[3]).user
	# 	response = self.client.post(self.generate_url)

	# 	user_profile = UserProfile.objects.get(user=user)

	# 	self.assertEqual(
	# 		response.status_code,
	# 		status.HTTP_201_CREATED
	# 		)
	# 	self.assertNotEqual(
	# 		user_profile.public_key,
	# 		b'',
	# 		msg="Public key was not generated"
	# 		)
		
	# 	msg = "This is such a wonderfully long string, sure hope it works as I intended it to"
	# 	pub_key = RSA.importKey(user_profile.public_key)
	# 	private_key = RSA.importKey(response.content)

	# 	emsg = pub_key.encrypt(msg.encode('utf-8'), 32)[0]
	# 	dmsg = private_key.decrypt(emsg).decode('utf-8')

	# 	self.assertEqual(
	# 		msg,
	# 		dmsg,
	# 		msg="encryption fail"
	# 		)

	# 	response = self.client.post(self.generate_url)
	# 	self.assertEqual(
	# 		response.status_code,
	# 		status.HTTP_400_BAD_REQUEST,
	# 		msg="Regenerated key"
	# 		)

	# def test_generate_patch_key(self):
	# 	token_list = self.generate_users_receive_tokens()

	# 	self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_list[3])
	# 	response = self.client.patch(self.generate_url)
	# 	self.assertEqual(
	# 		response.status_code,
	# 		status.HTTP_400_BAD_REQUEST,
	# 		msg="Regenerated key for new user" + str(response.data)
	# 		)

	# 	response = self.client.post(self.generate_url)


	# 	user = Token.objects.get(key=token_list[3]).user
	# 	user_profile = UserProfile.objects.get(user=user)
	# 	pub_key = RSA.importKey(user_profile.public_key)

	# 	msg = "This is such a wonderfully long string, sure hope it works as I intended it to"
	# 	emsg_old = pub_key.encrypt(msg.encode('utf-8'), 32)[0]

	# 	response = self.client.patch(self.generate_url)

	# 	user_profile = UserProfile.objects.get(user=user)
	# 	pub_key = RSA.importKey(user_profile.public_key)
	# 	emsg_new = pub_key.encrypt(msg.encode('utf-8'), 32)[0]

	# 	self.assertNotEqual(
	# 		emsg_old,
	# 		emsg_new,
	# 		msg="Encryption did not change"
	# 		)

	# 	private_key = RSA.importKey(response.content)
	# 	dmsg = private_key.decrypt(emsg_new).decode('utf-8')

	# 	self.assertEqual(
	# 		msg,
	# 		dmsg,
	# 		msg="Encryption failed"
	# 		)