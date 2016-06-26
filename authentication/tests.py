from django.test import Client
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from django.contrib.auth.models import User
from authentication.models import UserProfile
from report.models import Report, Document
from report.serializers import ReportSerializer

from Crypto.PublicKey import RSA
from base64 import b64decode
import random

class UserTests(APITestCase):

	username = 'test_user'
	password = 'test_password'

	list_of_users = ['user1','user2','user3','user4','user5']
	list_of_passwords = ['password1','password2', 'password3', 'password4', 'password5']
	email = 'richard.github@gmail.com'

	user_data = {"username":list_of_users[0],"password":list_of_passwords[0],"email":"fake@fake.com","testing":'True'}

	register_url = '/api/v1/register/'
	login_url = '/api/v1/login/'
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