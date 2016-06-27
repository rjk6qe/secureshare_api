from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import JsonResponse, HttpResponse
from django.core.servers.basehttp import FileWrapper
from django.core.exceptions import ObjectDoesNotExist

from django.core.mail import EmailMessage

from rest_framework import views, status
from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.authtoken.models import Token

from authentication.serializers import UserSerializer
from authentication.models import UserProfile
from authentication.permissions import site_manager_only

from Crypto.PublicKey import RSA
import tempfile

class RegisterView(views.APIView):
	permission_classes = (permissions.AllowAny, )
	serializer_class = UserSerializer

	def post(self, request):
		"""
		View takes in username and password to create a user object
		200 returned on success, 400 returned on username already existing
		"""
		serializer = self.serializer_class(data = request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(status = status.HTTP_201_CREATED)
		else:
			return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)

	def get(self,request):
		"""
		Temporary, don't need this method, I'd imagine
		"""
		serializer = self.serializer_class(User.objects.all(), many=True)
		return Response(serializer.data, status = status.HTTP_200_OK)

class LoginView(views.APIView):

	permission_classes = (permissions.AllowAny,)
	serializer_class = UserSerializer

	def post(self,request):
		"""
		View takes in username and password, returns token on successfull login
		NOTE: May want to create unique token for each login
		"""
		temp_username = request.data.get('username',None)
		temp_password = request.data.get('password',None)
		temp_user = authenticate( username=temp_username,password=temp_password)
	
		if temp_user is not None:
			new_token = Token.objects.get_or_create(user=temp_user)[0]
			temp_dict = { "token":new_token.key }
			return Response(temp_dict, status = status.HTTP_200_OK)
		else:
			return Response(
				{"Message":"Invalid credentials.",
				"Input username":temp_username,
				"Input password":temp_password}, 
				status = status.HTTP_401_UNAUTHORIZED
				)

class LogoutView(views.APIView):

	def get(self, request):
		try:
			Token.objects.get(user=request.user).delete()
			return Response({"Message":"User successfully logged out"}, status = status.HTTP_200_OK)
		except ObjectDoesNotExist:
			return Response({"Message":"User is not logged in"},status=status.HTTP_400_BAD_REQUEST)

		
class SiteManagerView(views.APIView):

	permission_classes = (site_manager_only, )
	queryset = UserProfile.objects.filter(site_manager=True)

	"""
	[{"username":"user1"},{"username":"user2"}]

	"""

	def post(self, request):
		user_list = request.data
		user_list_size = len(user_list)
		error_list = []
		success_list = []
		error = False
		for user in user_list:
			try:
				new_user = User.objects.get(username=user['username'])
				user_profile = UserProfile.objects.get(user=new_user)
				user_profile.site_manager = True
				user_profile.save()
				success_list.append(user['username'])
			except ObjectDoesNotExist:
				error = False
				error_list.append(user['username'])
		if error:
			return Response(
				[{"Message":"Some users could not be made site managers."},
				{"Failure":error_list},
				{"Success":success_list}],
				status = status.HTTP_400_BAD_REQUEST
				)
		return Response(status = status.HTTP_200_OK)

class GenerateView(views.APIView):

	email = 'richard.github@gmail.com'
	test_email = 'richard.github@gmail.com'

	def post(self, request):
		user = request.user
		user_profile = UserProfile.objects.get(user=user)
		if user_profile.public_key != b'':
			key = RSA.generate(2048)
			user_profile.public_key = key.publickey().exportKey('PEM')
			user_profile.save()
			temp = tempfile.NamedTemporaryFile(delete=True)
			try:
				print("trying")
				email = EmailMessage(
					subject="<IMPORTANT> Secureshare Private Key",
					body="Dear " + request.user.username + ",\n Attached is your private key. Store this in a safe place and do not delete it.",
					to=[self.email,]
					)
				temp.write(key.exportKey('PEM'))
				print("wrote key")
				temp.seek(0)
				file_name = user.username + '_private_key.pem'
				print('attaching')
				email.attach(file_name, temp.read(), 'application/pdf')
				print('done attaching')
				#response = HttpResponse(temp, content_type='application/download',status=status.HTTP_201_CREATED)
				#response['Content-Disposition'] = 'attachment; filename=%s"' % file_name
			finally:
				print("closing")
				print('sending')
				res = email.send(fail_silently=False)
				print('done sending')
				temp.close()

				return Response(res, status=status.HTTP_200_OK)
		else:
			return Response(
				{"Error":"Key already generated, submit PATCH request"}, 
				status = status.HTTP_400_BAD_REQUEST
				)

	def patch(self, request,pk=None):
		user = request.user
		user_profile = UserProfile.objects.get(user=user)
		if user_profile.public_key == b'':
			return Response(
				{"Error":"Submit POST to generate key"},
				status=status.HTTP_400_BAD_REQUEST
				)
		else:
			key = RSA.generate(2048)
			user_profile.public_key = key.publickey().exportKey('PEM')
			user_profile.save()
			temp = tempfile.NamedTemporaryFile(delete=True)
			try:
				temp.write(key.exportKey('PEM'))
				temp.seek(0)
				file_name = user.username + '_private_key.pem'
				response = HttpResponse(temp, content_type='application/download',status=status.HTTP_201_CREATED)
				response['Content-Disposition'] = 'attachment; filename=%s"' % file_name
			finally:
				temp.close()
				return response

# class UserViewSet(viewsets.ModelViewSet):
# 	serializer_class = UserSerializer
# 	queryset = User.objects.all()

# 	def list(self, request):
# 		return Response(self.serializer_class(self.queryset,many=True).data)

# Create your views here.