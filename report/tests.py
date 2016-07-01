from django.test import Client
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token

from authentication.models import UserProfile
from report.models import Report, Document, Folder
from report.serializers import ReportSerializer

import random
import json
import os

class ReportTests(APITestCase):

	list_of_users = ['user1','user2','user3']
	list_of_passwords = ['password1','password2', 'password3']

	register_url = '/api/v1/users/register/'
	login_url = '/api/v1/users/login/'
	reports_url = '/api/v1/reports/'
	folders_url = '/api/v1/reports/folders/'

	base_dir = '/home/richard/secureshare/temp_keys/'

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

	def test_post(self):
		token_list = self.generate_users_receive_tokens()
		
		user_one_token = token_list[0]
		user_two_token = token_list[1]
		user_three_token = token_list[2]

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])
		user_three = User.objects.get(username=self.list_of_users[2])

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_one_token))
		response = self.client.post(self.reports_url, {'data':json.dumps(self.public_report_data)},format='multipart')
		
		self.assertEqual(
			response.status_code,
			status.HTTP_201_CREATED,
			msg = "Incorrect response code when creating a valid report" + str(response.data)
			)

		file_list = response.data.pop('files')

		self.assertEqual(
			Report.objects.count(),
			1,
			msg="Report object not made after successful creation"
			)

		self.assertEqual(
			Report.objects.get().name,
			self.public_report_data['name'],
			msg="Created Report object has incorrect name"
			)

		self.assertEqual(
			Report.objects.get().short_description,
			self.public_report_data['short_description'],
			msg = "Created Report object has incorrect short description"
			)

		self.assertEqual(
			Report.objects.get().long_description,
			self.public_report_data['long_description'],
			msg = "Created Report object has incorrect long description"
			)	

	def test_post_files(self):
		token_list = self.generate_users_receive_tokens()
		
		user_one_token = token_list[0]
		user_two_token = token_list[1]
		user_three_token = token_list[2]

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])
		user_three = User.objects.get(username=self.list_of_users[2])

		file_one = self.base_dir + "file_one"
		file_one_content = "This is a test file, please work"
		file_two = self.base_dir + "file_two"
		file_two_content = "kas.jdfsf asdf .has as d///*&(* bunch of characters in it....skfsld;kaf2131"

		file_one_ptr = open(file_one,'wb+')
		file_one_ptr.write(bytes(file_one_content.encode('utf-8')))
		file_two_ptr = open(file_two,'wb+')
		file_two_ptr.write(bytes(file_two_content.encode('utf-8')))

		encrypted_list = [True, True]
		self.private_report_data['encrypted'] = encrypted_list

		files = {"file_one":file_one_ptr, "file_two":file_two_ptr}

		send_data = {'data':json.dumps(self.private_report_data),'file':[file_one_ptr,file_two_ptr]}

		self.client.credentials(HTTP_AUTHORIZATION="Token " + str(user_one_token))	
		response = self.client.post(
			self.reports_url,
			send_data,
			format='multipart'
			)

		self.assertEqual(
		 	response.status_code,
		 	status.HTTP_201_CREATED,
		 	msg="Incorrect response code when creating report with files" + str(response.data)
			)

		report = Report.objects.get()
		doc_list = report.files.all()

		self.assertEqual(
			len(doc_list),
			2,
			msg="Incorrect number of documents associated with report" + str(response.data)
			)

		os.remove(file_one)
		os.remove(file_two)

		for file in doc_list:
			os.remove("/home/richard/secureshare/secureshare/media/" + str(file.file))

	def test_get_private(self):
		token_list = self.generate_users_receive_tokens()
		
		user_one_token = token_list[0]
		user_two_token = token_list[1]
		user_three_token = token_list[2]

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])
		user_three = User.objects.get(username=self.list_of_users[2])

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_two_token))
		self.client.post(self.reports_url, {'data':json.dumps(self.private_report_data)}, format='json')

		response = self.client.get(self.reports_url)

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Valid user was unable to get list of reports"
			)

		self.assertEqual(
			response.data[0]['name'],
			self.private_report_data['name'],
			msg="List of reports does not match name"
			)

		self.assertEqual(
			response.data[0]['short_description'],
			self.private_report_data['short_description'],
			msg="List of reports does not match description"
			)

		self.assertEqual(
			response.data[0]['long_description'],
			self.private_report_data['long_description'],
			msg="List of reports does not match long description"
			)

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_three_token))
		response = self.client.get(self.reports_url)

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="A different user was denied a get request"
			)

		self.assertEqual(
			len(response.data),
			0,
			msg="A different user was able to see a private report"
			)

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_three_token))
		self.client.post(self.reports_url, {'data':json.dumps(self.public_report_data)}, format='json')

		response = self.client.get(self.reports_url)

		self.assertEqual(
			len(response.data),
			1,
			msg="User 3 get request returned incorrect number of reports"
			)

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_two_token))
		response = self.client.get(self.reports_url)

		self.assertEqual(
			len(response.data),
			2,
			msg="User 2 get request returned incorrect number of reports"
			)

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_one_token))
		response = self.client.get(self.reports_url)

		self.assertEqual(
			len(response.data),
			1,
			msg="User 1 get request returned incorrect number of reports"
			)

	def test_get_site_manager(self):
		token_list = self.generate_users_receive_tokens()
		
		user_one_token = token_list[0]
		user_two_token = token_list[1]
		user_three_token = token_list[2]

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])
		user_three = User.objects.get(username=self.list_of_users[2])

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_two_token))
		self.client.post(self.reports_url, {'data':json.dumps(self.private_report_data)}, format='json')

		profile = UserProfile.objects.get(user=user_one)
		profile.site_manager = True
		profile.save()

		response = self.client.get(self.reports_url)

		self.assertEqual(
			len(response.data),
			1,
			msg="Site manager could not see private report"
			)

	def test_get_by_id(self):
		token_list = self.generate_users_receive_tokens()
		
		user_one_token = token_list[0]
		user_two_token = token_list[1]
		user_three_token = token_list[2]

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])
		user_three = User.objects.get(username=self.list_of_users[2])

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_one_token))
		response = self.client.post(self.reports_url, {'data':json.dumps(self.public_report_data)}, format='json')
		pk = response.data['pk']

		response = self.client.get(self.reports_url + str(pk) + "/")

		response.data.pop('pk')
		response.data.pop('files')

		self.assertEqual(
			response.data['name'],
			self.public_report_data['name'],
			msg="Returned incorrect report information"
			)

		response = self.client.get(self.reports_url + "2/")

		self.assertEqual(
			response.status_code,
			status.HTTP_400_BAD_REQUEST,
			msg="Invalid id gave incorrect response code"
			)

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_two_token))
		response = self.client.post(self.reports_url, {'data':json.dumps(self.private_report_data)}, format='json')
		private_pk = response.data['pk']

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_one_token))
		response = self.client.get(self.reports_url + str(private_pk) + "/")

		self.assertEqual(
			response.status_code,
			status.HTTP_400_BAD_REQUEST,
			msg="Another user was able to request a private report"
			)

		profile = UserProfile.objects.get(user=user_three)
		profile.site_manager = True
		profile.save()

		self.client.credentials(HTTP_AUTHORIZATION='Token ' + str(user_three_token))
		response = self.client.get(self.reports_url + str(private_pk) + "/")

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Site manager denied request to a private report"
			)

	def test_delete(self):
		token_list = self.generate_users_receive_tokens()
		
		user_one_token = token_list[0]
		user_two_token = token_list[1]
		user_three_token = token_list[2]

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])
		user_three = User.objects.get(username=self.list_of_users[2])

		self.client.credentials(HTTP_AUTHORIZATION="Token " + str(user_one_token))
		self.client.post(self.reports_url, {'data':json.dumps(self.public_report_data)},format='multipart')

		self.client.credentials(HTTP_AUTHORIZATION="Token " + str(user_two_token))
		response = self.client.delete(self.reports_url+'1/')

		self.assertEqual(
			response.status_code,
			status.HTTP_400_BAD_REQUEST,
			msg="Incorrect status code when trying to delete another user's public report"
			)

		self.assertEqual(
			Report.objects.count(),
			1,
			msg="A user deleted another user's report"
			)

		self.client.credentials(HTTP_AUTHORIZATION="Token " + str(user_one_token))
		response = self.client.delete(self.reports_url+'1/')		

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Incorrect status code when a user tried to delete their report"
			)

		self.assertEqual(
			Report.objects.count(),
			0,
			msg="A user was not able to delete their own report"
			)

	def test_patch(self):
		token_list = self.generate_users_receive_tokens()
		
		user_one_token = token_list[0]
		user_two_token = token_list[1]
		user_three_token = token_list[2]

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])
		user_three = User.objects.get(username=self.list_of_users[2])

		self.client.credentials(HTTP_AUTHORIZATION="Token " + str(user_one_token))
		self.client.post(self.reports_url, {'data':json.dumps(self.public_report_data)},format='multipart')

		old = self.public_report_data['name']
		new = "this is a different field"
		self.public_report_data['name'] = new

		self.client.credentials(HTTP_AUTHORIZATION="Token " + str(user_one_token))
		response = self.client.patch(self.reports_url+'1/',{'data':json.dumps(self.public_report_data)})

		self.assertEqual(
			response.status_code,
			status.HTTP_200_OK,
			msg="Incorrect status code when a valid user tried to modify their report" + str(response.data)
			)

		self.assertEqual(
			Report.objects.get().name,
			new,
			msg="The report object name was not changed"
			)

		self.public_report_data['name'] = old

		self.client.credentials(HTTP_AUTHORIZATION="Token " + str(user_two_token))
		response = self.client.patch(self.reports_url+'1/',{'data':json.dumps(self.public_report_data)})

		self.assertEqual(
			response.status_code,
			status.HTTP_400_BAD_REQUEST,
			msg="Incorrect status code when a user was able to modify another user's report"
			)

		self.assertEqual(
			Report.objects.get().name,
			new,
			msg="A user was able to modify another user's report"
			)

	def test_folder_post(self):
		token_list = self.generate_users_receive_tokens()
		
		user_one_token = token_list[0]
		user_two_token = token_list[1]
		user_three_token = token_list[2]

		user_one = User.objects.get(username=self.list_of_users[0])
		user_two = User.objects.get(username=self.list_of_users[1])
		user_three = User.objects.get(username=self.list_of_users[2])

		self.client.credentials(HTTP_AUTHORIZATION="Token " + str(user_one_token))
		self.client.post(self.reports_url, {'data':json.dumps(self.public_report_data)},format='multipart')

		self.client.credentials(HTTP_AUTHORIZATION="Token " + str(user_two_token))
		self.client.post(self.reports_url, {'data':json.dumps(self.private_report_data)},format='multipart')

		response = self.client.get(self.reports_url)

		report_list = response.data
		pk_list = []
		
		for report in report_list:
			pk_list.append(report['pk'])

		data = {"name":"folder_name", "reports":pk_list}

		response = self.client.post(self.folders_url, data, format='json')

		self.assertEqual(
			response.status_code,
			status.HTTP_201_CREATED,
			msg="Incorrect response code when a user tried creating a folder"
			)

		self.assertEqual(
			Folder.objects.count(),
			1,
			msg="Folder object was not created"
			)

		self.assertEqual(
			Folder.objects.get().owner,
			user_two,
			msg="Folder object has incorrect owner"
			)

		self.assertEqual(
			len(Folder.objects.get().reports.all()),
			len(pk_list),
			msg="Folder object has incorrect number of reports"
			)

	# def test_patch(self):
	# 	token_list = self.generate_users_receive_tokens()
	# 	token = token_list[2]

	# 	self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
	# 	response = self.client.patch(self.reports_url, self.private_report_data, format='json')

	# 	self.assertEqual(
	# 		response.status_code,
	# 		status.HTTP_400_BAD_REQUEST
	# 		)

	# 	response = self.client.patch(self.reports_url + '1/', self.private_report_data, format='json')

	# 	self.assertEqual(
	# 		response.status_code,
	# 		status.HTTP_400_BAD_REQUEST
	# 		)

	# 	response = self.client.post(self.reports_url, self.private_report_data, format='json')
	# 	created_pk = response.data['pk']

	# 	self.client.credentials(HTTP_AUTHORIZATION='Token ' + token_list[1])
	# 	response = self.client.patch(self.reports_url + str(created_pk) + '/', self.private_report_data, format='json')

	# 	self.assertEqual(
	# 		response.status_code,
	# 		status.HTTP_401_UNAUTHORIZED,
	# 		msg="Accepted unauthorized request " + str(response.data)
	# 		)

	# 	self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
	# 	response = self.client.patch(self.reports_url + str(created_pk) + '/', self.public_report_data, format='json')

	# 	self.assertEqual(
	# 		response.status_code,
	# 		status.HTTP_202_ACCEPTED,
	# 		msg="Authorized request denied"
	# 		)
	# 	self.assertEqual(
	# 		response.data['name'],
	# 		self.private_report_data['name'],
	# 		msg="Incorrect field name"
	# 		)