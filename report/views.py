from django.shortcuts import render
from django.contrib.auth.models import User

from rest_framework import permissions, viewsets, status
from rest_framework.response import Response

from report.serializers import ReportSerializer#, MessageSerializer
from report.models import Report#, Message

class ReportViewSet(viewsets.ModelViewSet):
	serializer_class = ReportSerializer
	
	def get_queryset(self):
		user = self.request.user
		queryset = Report.objects.filter(owner = user)
		return queryset

	"""
	def create(self, request):
		serializer = self.serializer_class(data = request.data)
		if serializer.is_valid():
			serializer.save()
			return Response(serializer.validated_data)
		else:
			return Response({
				'status':'Bad request',
				'message':'Report could not be created'
				})
	
	def list(self, request):
		user = request.user
		queryset = Report.objects.filter(owner = user)
		serializer = ReportSerializer(queryset, many=True)
		return Response(serializer.data, status = status.HTTP_200_OK)
	"""

# Create your views here.
