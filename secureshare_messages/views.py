from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Q

from rest_framework import permissions, viewsets, status
from rest_framework.response import Response

from secureshare_messages.models import Message
from secureshare_messages.serializers import MessageSerializer

class MessageViewSet(viewsets.ModelViewSet):
	
	serializer_class = MessageSerializer

	def get_queryset(self):
		user = self.request.user
		queryset = Message.objects.filter(Q(sender = user) | Q(recipient = user))
		return queryset

# Create your views here.
