from django.test import Client
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from django.contrib.auth.models import User
from authentication.models import UserProfile
from secureshare_messages.models import Message

from Crypto.PublicKey import RSA
from base64 import b64decode
import random

class MessageTests(APITestCase):

	list_of_users = ['user1','user2']
	list_of_passwords = ['password1','password2']

	user_data = {"username":list_of_users[0],"password":list_of_passwords[0],"email":"fake@fake.com","testing":'True'}

	message_unencrypted_data = {
	"recipient" : "user2",
	"subject":"test message",
	"body":"hey what is up you whadfksdfdsl;faskdfas;kf",
	"encrypted":"False"
	}
	message_encrypted_data = {
	"recipient" : "user2",
	"subject" : "test message",
	"body":"hey what is up you whadfksdfdslfaskdfask",
	"encrypted":"True"
	}

	register_url = '/api/v1/register/'
	login_url = '/api/v1/login/'

	message_inbox_url = '/api/v1/messages/inbox/'
	message_send_url = '/api/v1/messages/send/'
	message_outbox_url = '/api/v1/messages/outbox/'

	def generate_users_receive_tokens(self):
		size_of_list = len(self.list_of_users)
		token_list = []
		
		for i in range(0, size_of_list):
			self.user_data['username'] = self.list_of_users[i]
			self.user_data['password'] = self.list_of_passwords[i]			
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
			token_list.append(response.data['token'])
		return token_list

	def test_send(self):
		token_list = self.generate_users_receive_tokens()

		user_one_token = token_list[0]
		user_two_token = token_list[1]
		
		self.client.credentials(HTTP_AUTHORIZATION='Token ' + user_one_token)
		response = self.client.post(self.message_send_url, data=self.message_unencrypted_data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Incorrect status code for valid message" + str(response.data)
			)

		self.assertEqual(
			Message.objects.count(),
			1,
			msg="Message not created"
			)
		self.assertEqual(
			Message.objects.get().body,
			self.message_unencrypted_data['body'],
			msg="Incorrect message' body"
			)
		self.assertEqual(
			Message.objects.get().subject,
			self.message_unencrypted_data['subject'],
			msg="Incorrect message subject"
			)
		self.assertEqual(
			Message.objects.get().sender,
			Token.objects.get(key=user_one_token).user,
			msg="Incorrect sender"
			)
		self.assertEqual(
			Message.objects.get().recipient,
			User.objects.get(username=self.message_unencrypted_data['recipient']),
			msg="Incorrect m'"
			)

		new_data = self.message_unencrypted_data
		new_data['recipient'] = "user_DNE"

		response = self.client.post(self.message_send_url, data=new_data, format='json')
		self.assertEqual(
			response.status_code,
			status.HTTP_400_BAD_REQUEST,
			msg="Invalid recipient was accepted"
			)
		self.assertEqual(
			Message.objects.count(),
			1,
			msg="A message was created for invalid message"
			)

	def test_send_encrypted(self):
		token_list = self.generate_users_receive_tokens()
		user_one_token = token_list[0]
		user_two_token = token_list[1]


		self.message_encrypted_data['recipient'] = "user2"
		self.client.credentials(HTTP_AUTHORIZATION='Token ' + user_one_token)
		response = self.client.post(self.message_send_url, data=self.message_encrypted_data,format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Encrypted message denied" + str(response.data)
			)
		self.assertEqual(
			Message.objects.count(),
			1,
			msg="Encrypted message not created"
			)
		self.assertNotEqual(
			Message.objects.get().subject,
			self.message_encrypted_data['subject'],
			msg="Subject was not encrypted"	
			)
		self.assertNotEqual(
			Message.objects.get().body,
			self.message_encrypted_data['body'],
			msg="Body was not encrypted"
			)


	def test_get(self):
		token_list = self.generate_users_receive_tokens()

		user_one_token = token_list[0]
		user_two_token = token_list[1]

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + user_one_token)
		self.client.post(self.message_send_url, data=self.message_unencrypted_data, format='json')

		response = self.client.get(self.message_outbox_url)
		
		self.assertEqual(
			len(response.data),
			1,
			msg="Message not in sender outbox"
			)

		response = self.client.get(self.message_inbox_url)

		self.assertEqual(
			len(response.data),
			0,
			msg="Incorrect number of messages in sender inbox"
			)

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + user_two_token)
		response = self.client.get(self.message_inbox_url)

		self.assertEqual(
			len(response.data),
			1,
			msg="Incorrect number of messages in recipient inbox"
			)

		response = self.client.get(self.message_outbox_url)

		self.assertEqual(
			len(response.data),
			0,
			msg="Incorrect number of messages in recipient outbox"
			)