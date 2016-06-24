from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import JsonResponse, HttpResponse
from django.core.servers.basehttp import FileWrapper

from rest_framework import views, status
from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.authtoken.models import Token

from authentication.serializers import UserSerializer
from authentication.models import UserProfile

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
			temp_token = Token.objects.get(user=temp_user)
			temp_dict = { "token":temp_token.key }
			return Response(temp_dict, status = status.HTTP_200_OK)
		else:
			return Response("ERROR: invalid username or password", status = status.HTTP_401_UNAUTHORIZED)
		
class GenerateView(views.APIView):

	def post(self, request):
		user = request.user
		user_profile = UserProfile.objects.get(user=user)
		if user_profile.public_key == b'':
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