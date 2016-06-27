from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import permissions, viewsets, status, views
from rest_framework.response import Response

from rest_framework.authtoken.models import Token

from authentication.models import UserProfile
from secureshare_messages.models import Message
from secureshare_messages.serializers import MessageSerializer

from Crypto.PublicKey import RSA
import requests
import ast

class MessageInboxView(views.APIView):

	serializer_class = MessageSerializer

	inbox_error = Response(
		{"Error":"Given key is not in user's inbox"},
		status = status.HTTP_400_BAD_REQUEST
		)

	def get(self, request, pk=None):
		if 'pk' in self.kwargs:
			pk = self.kwargs['pk']
			try:
				message = Message.objects.get(pk=pk)
				serializer = self.serializer_class(message)
				if serializer.is_valid():
					if message.recipient == request.user:
						return Response(
							serializer.data,
							status = status.HTTP_200_OK
							)
				return self.inbox_error
			except ObjectDoesNotExist:
				return self.inbox_error
		else:
			queryset = Message.objects.filter(recipient=request.user)
			serializer = self.serializer_class(queryset, many=True)
			return Response(serializer.data,status=status.HTTP_200_OK)

	def delete(self, request, pk=None):
		if 'pk' not in self.kwargs:
			return Response(
				{"Message":"Must specify which key to delete"},
				status=status.HTTP_400_BAD_REQUEST
				)
		else:
			pk = self.kwargs['pk']
			try:
				message = Message.objects.get(pk=pk)
				if message.recipient == request.user:
					message.delete()
					return Response(
						{"Message":"Message deleted"},
						status=status.HTTP_200_OK
						)
				else:
					return Response(
						{"Message":"You do not own this message"},
						status = status.HTTP_400_BAD_REQUEST
						)
			except ObjectDoesNotExist:
				return self.inbox_error
			
class MessageSendView(views.APIView):

	serializer_class = MessageSerializer
	
	def post(self, request):
		serializer = self.serializer_class(data=request.data)
		if serializer.is_valid():
			recipient = request.data.get('recipient',None)
			try:
				recipient_user = User.objects.get(username=recipient)
				user_profile = UserProfile.objects.get(user=recipient_user)
				serializer.save(sender=request.user, recipient=recipient_user)
				return Response(
					{"Message":"Message sent"},
					status=status.HTTP_200_OK
					)
			except ObjectDoesNotExist:
				return Response(
					{"Error":"Recipient does not exist"},
					status = status.HTTP_400_BAD_REQUEST,
					)
		else:
			return Response(
				serializer.errors,
				status = status.HTTP_400_BAD_REQUEST
				)

class MessageOutboxView(views.APIView):
	serializer_class = MessageSerializer
	def get(self, request):
		queryset = Message.objects.filter(sender=request.user)
		serializer = self.serializer_class(queryset, many=True)
		return Response(
			serializer.data,
			status=status.HTTP_200_OK
			)

class MessageDecryptView(views.APIView):

	serializer_class = MessageSerializer

	def post(self, request, pk=None):
		if 'pk' not in self.kwargs:
			return Response(
				{"Message":"Must specify which message to decrypt"},
				status=status.HTTP_400_BAD_REQUEST
				)
		pk = self.kwargs['pk']
		try:
			msg = Message.objects.get(pk=pk)
			if not msg.recipient == request.user:
				raise ObjectDoesNotExist
			file = request.FILES.get('private_key',None)
			if file is None:
				return Response({"Message":"No private key uploaded"},status=status.HTTP_400_BAD_REQUEST)
			try:
				private_key = RSA.importKey(file.read())
				d_msg_subject = private_key.decrypt(ast.literal_eval(msg.subject)).decode('utf-8')
				d_msg_body = private_key.decrypt(ast.literal_eval(msg.body)).decode('utf-8')
				msg_dict = {"subject":d_msg_subject, "body":d_msg_body}
				decrypted_msg = self.serializer_class(data=msg_dict)
				if decrypted_msg.is_valid():
					return Response(decrypted_msg.data, status = status.HTTP_200_OK)
				else:
					return Response({"Message":"Message was not decrypted"},status = status.HTTP_400_BAD_REQUEST)

			except (IndexError, ValueError):
				return Response({"Message":"Invalid Key"}, status = status.HTTP_400_BAD_REQUEST)
		except ObjectDoesNotExist:
			return Response(
				{"Message":"Either invalid message id or user cannot decrypt this message"},
				status = status.HTTP_400_BAD_REQUEST
				)