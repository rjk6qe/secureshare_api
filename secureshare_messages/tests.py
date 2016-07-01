from django.test import Client
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from authentication.models import UserProfile
from secureshare_messages.models import Message
from secureshare_messages.serializers import MessageSerializer

from Crypto.PublicKey import RSA
from base64 import b64decode
import random

class MessageTests(APITestCase):

	list_of_users = ['user1','user2','user3']
	list_of_passwords = ['password1','password2','password3']

	user_data = {"username":list_of_users[0],"password":list_of_passwords[0],"email":"fake@fake.com","testing":'True'}

	test_keys_base = '/home/richard/secureshare/temp_keys/'

	message_unencrypted_data = {
		"recipient" : list_of_users[1],
		"subject":"test message",
		"body":"hey what is up you whadfksdfdsl;faskdfas;kf",
		"encrypted":"False"
		}

	message_encrypted_data = {
		"recipient" : list_of_users[1],
		"subject" : "test message",
		"body":"hey what is up you whadfksdfdslfaskdfask",
		"encrypted":"True"
		}

	register_url = '/api/v1/users/register/'
	login_url = '/api/v1/users/login/'

	message_inbox_url = '/api/v1/messages/inbox/'
	message_send_url = '/api/v1/messages/send/'
	message_outbox_url = '/api/v1/messages/outbox/'
	message_decrypt_url = '/api/v1/messages/decrypt/'


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

	def register_new_users(self):
		size_of_list = len(self.list_of_users)
		token_list = []
		
		for i in range(0, size_of_list):
			data = {"username":self.list_of_users[i], "password":self.list_of_users[i]}
			response = self.client.post(self.register_url, data, format='json')
			self.assertEqual(
				response.status_code,
				status.HTTP_201_CREATED
				)
			response = self.client.post(self.login_url, data, format='json')
			token_list.append(response.data['key'])

		return token_list

	def test_send_unencrypted_incorrect(self):
		token_list = self.generate_users_receive_tokens()
		
		user_one_token = token_list[0]
		user_two_token = token_list[1]
		user_three_token = token_list[2]

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])
		user_three = User.objects.get(username=self.list_of_users[2])

		self.message_unencrypted_data['recipient'] = "user_DNE"

		self.client.credentials(HTTP_AUTHORIZATION="Token " + user_one_token)
		response = self.client.post(self.message_send_url, self.message_unencrypted_data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_400_BAD_REQUEST,
			msg="Message with nonexistent recipient was accepted"
			)
		self.assertEqual(
			Message.objects.count(),
			0,
			msg="Message object created for failed message"
			)

	def test_send_unencrypted(self):
		token_list = self.generate_users_receive_tokens()
		
		user_one_token = token_list[0]
		user_two_token = token_list[1]
		user_three_token = token_list[2]

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])
		user_three = User.objects.get(username=self.list_of_users[2])


		self.message_unencrypted_data['recipient'] = user_two.username

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_one_token))
		response = self.client.post(self.message_send_url, self.message_unencrypted_data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Sending valid message returned incorrect response code" + str(response.data)
			)

		self.assertEqual(
			Message.objects.count(),
			1,
			msg="Message object not created after sending"
			)

		self.assertEqual(
			Message.objects.get().body,
			self.message_unencrypted_data['body'],
			msg="Message object has incorrect body"
			)
		
		self.assertEqual(
			Message.objects.get().subject,
			self.message_unencrypted_data['subject'],
			msg="Message object has incorrect subject"
			)

		self.assertEqual(
			Message.objects.get().sender,
			user_one,
			msg="Message object has incorrect sender"
			)

		self.assertEqual(
			Message.objects.get().recipient,
			user_two,
			msg="Message object has incorrect recipient"
			)

	def test_send_encrypted_incorrect(self):
		token_list = self.generate_users_receive_tokens()
		
		user_one_token = token_list[0]
		user_two_token = token_list[1]
		user_three_token = token_list[2]

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])
		user_three = User.objects.get(username=self.list_of_users[2])

		self.client.credentials(HTTP_AUTHORIZATION="Token " + str(user_one_token))
		response = self.client.post(self.message_send_url, self.message_encrypted_data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_400_BAD_REQUEST,
			msg="Incorrect response when sending message to user with no public key"
			)

	def test_send_encrypted(self):
		token_list = self.register_new_users()
		
		user_one_token = token_list[0]
		user_two_token = token_list[1]
		user_three_token = token_list[2]

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])
		user_three = User.objects.get(username=self.list_of_users[2])


		self.message_encrypted_data['recipient'] = user_two.username

		self.client.credentials(HTTP_AUTHORIZATION="Token " + str(user_one_token))
		response = self.client.post(self.message_send_url, self.message_encrypted_data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Incorrect status code returned when sending valid encrypted message" + str(response.data)
			)
		
		self.assertEqual(
			Message.objects.count(),
			1,
			msg="Message object not created when sending encrypted message"
			)

		self.assertNotEqual(
			Message.objects.get().subject,
			self.message_encrypted_data['subject'],
			msg="Encrypted message subject matches original"	
			)
		
		self.assertNotEqual(
			Message.objects.get().body,
			self.message_encrypted_data['body'],
			msg="Encrypted message body matches original"
			)

	def test_decrypt_message(self):
		token_list = self.register_new_users()
		
		user_one_token = token_list[0]
		user_two_token = token_list[1]
		user_three_token = token_list[2]

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])
		user_three = User.objects.get(username=self.list_of_users[2])

		user_one_private_key = self.test_keys_base + user_one.username + '_private_key.pem'
		user_two_private_key = self.test_keys_base + user_two.username + '_private_key.pem'

		self.message_encrypted_data['recipient'] = user_two.username

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_one_token))
		response = self.client.post(self.message_send_url, self.message_encrypted_data,format='json')

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_two_token))
		response = self.client.get(self.message_inbox_url)

		msg_data = response.data[0]
		msg_pk = msg_data['pk']

		fake_key = self.test_keys_base + user_one.username + '_private_key.pem'
		with open(user_one_private_key,'w') as f:
			f.write("this is not a PEM file")
		with open(user_two_private_key,'rb') as f:
			self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_two_token))
			response = self.client.post(self.message_decrypt_url + str(msg_pk) + '/', {"private_key":f}, format='multipart')

		decrypted_message = response.data
		
		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Incorrect response code when decrypting message" + str(response.data)
			)

		self.assertEqual(
			decrypted_message['subject'],
			self.message_encrypted_data['subject'],
			msg="Decrypted subject is not correct"
			)

		self.assertEqual(
			decrypted_message['body'],
			self.message_encrypted_data['body'],
			msg="Decrypted body is not correct"
			)

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_one_token))
		response = self.client.post(self.message_decrypt_url + str(msg_pk) + '/', {"private_key":user_two_private_key}, format='multipart')

		self.assertEqual(
			response.status_code,
			status.HTTP_400_BAD_REQUEST,
			msg="Incorrect response code when trying to decrypt a message not sent to the requesting user"
			)

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_two_token))
		response = self.client.post(self.message_decrypt_url + str(msg_pk) + '/', {"private_key":user_one_private_key}, format='multipart')
		
		self.assertEqual(
			response.status_code,
			status.HTTP_400_BAD_REQUEST,
			msg="Accepted incorrect key for decryption"
			)


	# def test_get(self):
	# 	token_list = self.generate_users_receive_tokens()

	# 	user_one_token = token_list[0]
	# 	user_two_token = token_list[1]

	# 	self.client.credentials(HTTP_AUTHORIZATION='Token ' + user_one_token)
	# 	self.client.post(self.message_send_url, data=self.message_unencrypted_data, format='json')

	# 	response = self.client.get(self.message_outbox_url)
		
	# 	self.assertEqual(
	# 		len(response.data),
	# 		1,
	# 		msg="Message not in sender outbox"
	# 		)

	# 	response = self.client.get(self.message_inbox_url)

	# 	self.assertEqual(
	# 		len(response.data),
	# 		0,
	# 		msg="Incorrect number of messages in sender inbox"
	# 		)

	# 	self.client.credentials(HTTP_AUTHORIZATION='Token ' + user_two_token)
	# 	response = self.client.get(self.message_inbox_url)

	# 	self.assertEqual(
	# 		len(response.data),
	# 		1,
	# 		msg="Incorrect number of messages in recipient inbox"
	# 		)

	# 	response = self.client.get(self.message_outbox_url)

	# 	self.assertEqual(
	# 		len(response.data),
	# 		0,
	# 		msg="Incorrect number of messages in recipient outbox"
	# 		)