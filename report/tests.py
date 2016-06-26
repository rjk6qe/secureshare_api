from django.test import Client
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token

from django.contrib.auth.models import User
from authentication.models import UserProfile
from report.models import Report, Document
from report.serializers import ReportSerializer

import random
import json


class ReportTests(APITestCase):

	list_of_users = ['user1','user2','user3','user4','user5']
	list_of_passwords = ['password1','password2', 'password3', 'password4', 'password5']

	register_url = '/api/v1/users/register/'
	login_url = '/api/v1/users/login/'
	reports_url = '/api/v1/reports/'

	private_report_data = { "name": "This is a Report", 
	"short_description" : "This is a short description",
	"long_description" : "This is a long description",
	"private":"True"
	}
	public_report_data = {"name": "This is a Report", 
	"short_description": "This is a short description",
	"long_description":"This is a long description people can see",
	"private":"False"
	}

	serializer_class = ReportSerializer


	def generate_users_receive_tokens(self):
		size_of_list = len(self.list_of_users)
		
		for i in range(0, size_of_list):
			data = {"username": self.list_of_users[i], "password": self.list_of_passwords[i]}
			self.client.post(self.register_url, data, format='json')

		self.assertEqual(
			User.objects.count(),
			size_of_list,
			msg="Users not created"
			)

		token_list = []
		data = {}

		for i in range(0, size_of_list):
			data = {"username": self.list_of_users[i], "password" : self.list_of_passwords[i]}
			response = self.client.post(self.login_url, data, format='json')
			self.assertEqual(
				response.status_code,
				status.HTTP_200_OK,
				msg="invalid user"
				)
			token_list.append(response.data['token'])
		return token_list

	def test_post(self):
		token_list = self.generate_users_receive_tokens()
		size_of_list = len(token_list)
		index = random.randint(0, size_of_list-1)
		token = token_list[index]
		model_token = Token.objects.get(key=token)
		user = model_token.user

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(model_token.key))
		response = self.client.post(self.reports_url, self.public_report_data, format='json')

		pk = response.data.pop('pk')
		file_list = response.data.pop('files')

		self.assertEqual(
			response.status_code,
			status.HTTP_201_CREATED,
			msg = "Incorrect status code"
			)

		try:
			r = Report.objects.get(pk=pk)
		except ObjectDoesNotExist:
			self.fail("Invalid private key")

		self.assertEqual(
			response.data['name'],
			self.public_report_data['name'],
			msg="Incorrect report name"
			)
		self.assertEqual(
			response.data['short_description'],
			self.public_report_data['short_description'],
			msg = "Incorrect short description"
			)
		self.assertEqual(
			response.data['long_description'],
			self.public_report_data['long_description'],
			msg = "Incorrect long description"
			)

		self.client.credentials()

		response = self.client.post(self.reports_url, self.public_report_data, format='json')
		self.assertEqual(
			response.status_code,
			status.HTTP_401_UNAUTHORIZED,
			msg="Incorrect status code for unauthorized request"
			)

	def test_get(self):
		token_list = self.generate_users_receive_tokens()
		site_manager_token = token_list[0]
		reporter_one_token = token_list[1]
		reporter_two_token = token_list[2]

		user_site_manager = Token.objects.get(key=site_manager_token).user
		user_profile = UserProfile.objects.get(user=user_site_manager)
		user_profile.site_manager = True
		user_profile.save()

		user_1 = Token.objects.get(key=reporter_one_token).user
		user_2 = Token.objects.get(key=reporter_two_token).user


		self.client.credentials(HTTP_AUTHORIZATION='Token ' + reporter_one_token)
		self.client.post(self.reports_url, self.private_report_data, format='json')

		response = self.client.get(self.reports_url)
		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Incorrect status code"
			)
		self.assertEqual(
			response.data[0]['name'],
			self.private_report_data['name'],
			msg="Incorrect name"
			)
		self.assertEqual(
			response.data[0]['short_description'],
			self.private_report_data['short_description'],
			msg="Incorrect short description"
			)
		self.assertEqual(
			response.data[0]['long_description'],
			self.private_report_data['long_description'],
			msg="Incorrect long description"
			)
		self.assertEqual(
			response.data[0]['pk'],
			1,
			msg="Incorrect private key"
			)
		self.assertEqual(
			Report.objects.count(),
			1,
			msg="Incorrect number of reports"
			)

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + reporter_two_token)

		response = self.client.get(self.reports_url)
		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Incorrect status code" + str(response.data)
			)
		self.assertEqual(
			len(response.data),
			0,
			msg="Incorrect number of reports"
			)

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + site_manager_token)
		response = self.client.get(self.reports_url)

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Site manager was denied access"
			)
		self.assertEqual(
			len(response.data),
			1,
			msg="Incorrect number of reports"
			)		

		response = self.client.get(self.reports_url + '2/')
		self.assertEqual(
			response.status_code,
			status.HTTP_400_BAD_REQUEST,
			msg="invalid private key results in incorrect status code"
			)

		response = self.client.get(self.reports_url + '1/')

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="SM: correct private key results in incorrect status code"
			)

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + reporter_two_token)
		response = self.client.get(self.reports_url + '1/')

		self.assertEqual(
			response.status_code,
			status.HTTP_401_UNAUTHORIZED,
			msg="unauthorized user was given access"
			)

		self.client.post(self.reports_url, self.private_report_data, format='json')
		self.client.credentials(HTTP_AUTHORIZATION='Token ' + reporter_one_token)
		response = self.client.get(self.reports_url)
		self.assertEqual(
			len(response.data),			
			1,
			msg="Incorrect number of reports"
			)
		self.client.credentials(HTTP_AUTHORIZATION='Token ' + site_manager_token)
		response = self.client.get(self.reports_url)
		self.assertEqual(
			len(response.data),			
			2,
			msg="Incorrect number of reports"
			)

	def test_patch(self):
		token_list = self.generate_users_receive_tokens()
		token = token_list[2]

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
		response = self.client.patch(self.reports_url, self.private_report_data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_400_BAD_REQUEST
			)

		response = self.client.patch(self.reports_url + '1/', self.private_report_data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_400_BAD_REQUEST
			)

		response = self.client.post(self.reports_url, self.private_report_data, format='json')
		created_pk = response.data['pk']

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_list[1])
		response = self.client.patch(self.reports_url + str(created_pk) + '/', self.private_report_data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_401_UNAUTHORIZED,
			msg="Accepted unauthorized request " + str(response.data)
			)

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
		response = self.client.patch(self.reports_url + str(created_pk) + '/', self.public_report_data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_202_ACCEPTED,
			msg="Authorized request denied"
			)
		self.assertEqual(
			response.data['name'],
			self.private_report_data['name'],
			msg="Incorrect field name"
			)