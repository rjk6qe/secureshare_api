from django.shortcuts import render
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate
from django.http import JsonResponse, HttpResponse
from django.core.servers.basehttp import FileWrapper
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage

from rest_framework import views, status
from rest_framework.response import Response
from rest_framework import authentication, permissions
from rest_framework.authtoken.models import Token

from authentication.serializers import UserSerializer, UserProfileSerializer, GroupSerializer, SiteManagerSerializer, TokenSerializer
from authentication.models import UserProfile
from authentication.permissions import site_manager_only

from Crypto.PublicKey import RSA
import tempfile

class RegisterView(views.APIView):
	permission_classes = (permissions.AllowAny, )
	serializer_class = UserSerializer
	profile_class = UserProfileSerializer
	def post(self, request):
		"""
		View takes in username and password to create a user object
		200 returned on success, 400 returned on username already existing
		"""
		serializer = self.serializer_class(data = request.data)
		if serializer.is_valid():
			user = serializer.save()
			serializer = self.profile_class(data={})
			if serializer.is_valid():
				serializer.save(user=user)
				return Response(serializer.data, status = status.HTTP_201_CREATED)
			else:
				return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
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
	token_serializer = TokenSerializer
	def post(self,request):
		"""
		View takes in username and password, returns token on successfull login
		NOTE: May want to create unique token for each login
		"""
		temp_username = request.data.get('username', None)
		temp_password = request.data.get('password', None)
		temp_user = authenticate(
			username=temp_username,
			password=temp_password
			)
	
		if temp_user is not None:
			new_token = Token.objects.get_or_create(user=temp_user)[0]			
			return Response(
				self.token_serializer(new_token).data,
				status = status.HTTP_200_OK
				)
		else:
			return Response(
				{"Message":"Invalid credentials"},
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
	#queryset = UserProfile.objects.filter(site_manager=True)
	serializer_class = SiteManagerSerializer

	"""
	users:[{"username":"user1"},{"username":"user2"}], site_manager:true/false, active: true/false

	"""

	def post(self, request):
		serializer = self.serializer_class(data=request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(
				serializer.data,
				status=status.HTTP_200_OK
				)
		else:
			return Response(
				serializer.errors,
				status = status.HTTP_400_BAD_REQUEST
				)


class GroupView(views.APIView):

	serializer_class = GroupSerializer

	"""
	'pk':2, 'name':'groups are fun', users':[user1, user2,], 'delete':true/false
	"""

	def post(self, request):
		serializer = self.serializer_class(
			data=request.data,
			context={'action':'create','user':request.user}
			)
		if serializer.is_valid():
			serializer.save(owner=request.user)
			return Response(
				{"Message":"Group successfully created"},
				status = status.HTTP_201_CREATED
				)
		else:
			return Response(
				{"Message":"Group could not be created",
				"Errors":serializer.errors},
				status = status.HTTP_400_BAD_REQUEST
				)

	def patch(self, request):
		try:
			group_name = request.data.get('name')
			group = Group.objects.get(name=group_name)
			user_profile = UserProfile.objects.get(user=request.user)
			user_groups = request.user.groups.all()
			
			if (group in user_groups) or (user_profile.site_manager):
				serializer = self.serializer_class(
					group,
					data=request.data,
					context={'action':'update','user':request.user}
					)
				if serializer.is_valid():
					serializer.save()
					return Response(
						{"Message":"Group successfully modified"},
						status=status.HTTP_200_OK
						)
				else:
					return Response(
						serializer.errors,
						status=status.HTTP_400_BAD_REQUEST
						)
			raise ObjectDoesNotExist
		except ObjectDoesNotExist:
			return Response(
				{"Message":"User does not have permission to modify this group"},
				status=status.HTTP_400_BAD_REQUEST
				)