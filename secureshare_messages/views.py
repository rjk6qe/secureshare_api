from django.shortcuts import render
from django.contrib.auth.models import User

from rest_framework import permissions, viewsets, status
from rest_framework.response import Response

from secureshare_messages.models import Message
from secureshare_messages.serializers import MessageSerializer

class MessageViewSet(viewsets.ModelViewSet):
	queryset = Message.objects.all()
	serializer_class = MessageSerializer

	def list(self, request):
		pass
	

# Create your views here.
