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
		type = request.GET.get('request_type',"Inbox")

		if 'pk' in self.kwargs:
			pk = self.kwargs['pk']
			try:
				message = Message.objects.get(pk=pk)
				serializer = self.serializer_class(message)
				if message.sender == request.user:
					return Response(
						serializer.data,
						status = status.HTTP_200_OK
						)
				raise ObjectDoesNotExist
			except ObjectDoesNotExist:
				return Response(
					{"Message":"Given key not in user's inbox"},
					status = HTTP_400_BAD_REQUEST
					)
		
		queryset = Message.objects.filter(recipient=request.user)
		serializer = self.serializer_class(queryset, many=True)
		return Response(
			serializer.data,
			status=status.HTTP_200_OK
			)

	def delete(self, request, pk=None):
		if 'pk' not in self.kwargs:
			return Response(
				{"Message":"Must specify which key to delete"},
				status=status.HTTP_400_BAD_REQUEST
				)
		pk = self.kwargs['pk']
		try:
			message = Message.objects.get(pk=pk)
			if message.recipient == request.user:
				message.delete()
				return Response(
					{"Message":"Message deleted"},
					status=status.HTTP_200_OK
					)
			raise ObjectDoesNotExist
		except ObjectDoesNotExist:
			return Response(
				{"Message":"Given key not in user's inbox"},
				status = HTTP_400_BAD_REQUEST
				)
				

class MessageSendView(views.APIView):

	serializer_class = MessageSerializer
	
	def post(self, request):
		serializer = self.serializer_class(data=request.data)
		if serializer.is_valid():
			serializer.save(sender=request.user)
			return Response(
				{"Message":"Message sent"},
				status=status.HTTP_200_OK
				)
		return Response(
			{"Error":serializer.errors},
			status = status.HTTP_400_BAD_REQUEST
			)

class MessageOutboxView(views.APIView):
	serializer_class = MessageSerializer
	def get(self, request,pk=None):
		if 'pk' in self.kwargs:
			pk = self.kwargs['pk']
			try:
				message = Message.objects.get(pk=pk)
				if message.sender == request.user:
					serializer = self.serializer_class(message)
					return Response(
						serializer.data,
						status = status.HTTP_200_OK
						)
				raise ObjectDoesNotExist
			except ObjectDoesNotExist:
				return Response(
					{"Message":"Given key is not in user's outbox"},
					status = status.HTTP_400_BAD_REQUEST
					)
		queryset = Message.objects.filter(sender=request.user)
		serializer = self.serializer_class(queryset, many=True)
		return Response(
			{"Error":serializer.errors},
			status=status.HTTP_200_OK
			)

class MessageDecryptView(views.APIView):

	serializer_class = MessageSerializer

	def decrypt_message(self, private_key, msg):
		new_status = status.HTTP_200_OK
		error = False
		try:
			private_key = RSA.importKey(private_key)
			d_msg_subject = private_key.decrypt(ast.literal_eval(msg.subject)).decode('utf-8')
			d_msg_body = private_key.decrypt(ast.literal_eval(msg.body)).decode('utf-8')
			msg.body = d_msg_body
			msg.subject = d_msg_subject
		except (IndexError, ValueError):
			new_status = status.HTTP_400_BAD_REQUEST

		return Response(
			self.serializer_class(msg).data,
			status=new_status
			)


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
				return Response(
					{"Message":"No private key uploaded"},
					status=status.HTTP_400_BAD_REQUEST
					)
			
			return self.decrypt_message(file.read(), msg)

		except ObjectDoesNotExist:
			return Response(
				{"Message":"Either invalid message id or user cannot decrypt this message"},
				status = status.HTTP_400_BAD_REQUEST
				)