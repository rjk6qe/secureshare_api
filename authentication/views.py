from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import JsonResponse

from rest_framework import views, status
from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.authtoken.models import Token

from authentication.serializers import UserSerializer


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
			return Response(serializer.data, status = status.HTTP_201_CREATED)
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
		

# class UserViewSet(viewsets.ModelViewSet):
# 	serializer_class = UserSerializer
# 	queryset = User.objects.all()

# 	def list(self, request):
# 		return Response(self.serializer_class(self.queryset,many=True).data)

# Create your views here.