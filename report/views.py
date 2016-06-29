from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import permissions, viewsets, status, views
from rest_framework.response import Response

from report.serializers import ReportSerializer, FolderSerializer
from report.models import Report, Document#, Message
from authentication.models import UserProfile

class ReportView(views.APIView):
	"""
	Create new report using POST
	File uploads are done with PUT after the POST has already occured
	"""
	serializer_class = ReportSerializer

	def unique_report(self, user, report_name):
		report_query = Report.objects.filter(name=report_name)
		if report_query is None:
			return True
		for report in report_query:
			if report.owner == user:
				return False
		return True

	def get(self,request,pk=None):			
		"""
		For listing data
		"""
		user = self.request.user
		if not user.is_anonymous():
			user_profile = UserProfile.objects.get(user=user)
			if 'pk' in self.kwargs:
				try:
					selected = Report.objects.get(pk=self.kwargs['pk'])
					if selected.owner == request.user or selected.private == False or user_profile.site_manager:
						return Response(
							self.serializer_class(selected).data,
							status=status.HTTP_200_OK
							)

				except ObjectDoesNotExist:
					return Response(
						status=status.HTTP_400_BAD_REQUEST
						)
			else:
				if user_profile.site_manager:
					queryset = Report.objects.all()
				else:
					queryset = Report.objects.filter(
						Q(owner = user) | Q(private=False)
						)
				return Response(
					self.serializer_class(queryset, many=True).data,
					status = status.HTTP_200_OK
					)
		return Response(
			status=status.HTTP_401_UNAUTHORIZED
			)

	def post(self, request,pk=None):
		"""
		For creating reports
		"""
		if 'pk' in self.kwargs:
			return Response(
				{"Error":"Cannot specify key for POST operations"},
				status=status.HTTP_400_BAD_REQUEST
				)
		serializer = self.serializer_class(data = request.data)
		if serializer.is_valid():
			if self.unique_report(request.user, serializer.validated_data['name']):
				r = serializer.save(owner=request.user)
				return Response(
					serializer.data,
					status = status.HTTP_201_CREATED
					)
			else:
				return Response(
					{'Error':'User already created this report'},
					status = status.HTTP_400_BAD_REQUEST
					)
		else:
			return Response(
				serializer.errors,
				status = status.HTTP_400_BAD_REQUEST
				)

	def put(self, request,pk=None):
		"""
		For uploading files for already existing reports
		"""
		if 'pk' not in self.kwargs:
			return Response(
				{"Error":"Must supply key to existing Report"},
				status = status.HTTP_400_BAD_REQUEST
				)
		pk = self.kwargs['pk']
		try:
			report = Report.objects.get(pk=pk)
			if report.owner != request.user: #or has permission to do so
				return Response(
					{"message":"does not have permission to modify this report"},
					status=status.HTTP_400_BAD_REQUEST
					)
			response_dict = []
			for filename in request.FILES.getlist('file'):
				new_doc = Document(file = filename)
				new_doc.save()
				response_dict.append({'file_id':new_doc.pk})
				report.files.add(new_doc)
			return Response(
				response_dict,
				status = status.HTTP_202_ACCEPTED
				)
		except ObjectDoesNotExist:
			return Response(
				{"message":"code does not correspond to a valild report"},
				status = status.HTTP_400_BAD_REQUEST
				)

	def patch(self, request, pk=None):
		"""
		For updating existing report fields
		NOTE: Delete files not implemented
		"""
		if 'pk' not in self.kwargs:
			return Response(
				status = status.HTTP_400_BAD_REQUEST,
				)
		try:
			report = Report.objects.get(pk=self.kwargs['pk'])
			if report.owner != request.user:
				return Response(status = status.HTTP_401_UNAUTHORIZED)
			serializer = self.serializer_class(report, data = request.data)
			if serializer.is_valid():
				serializer.save()
				return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
			else:
				return Response(serializer.errors,status = status.HTTP_400_BAD_REQUEST)
		except ObjectDoesNotExist:
			return Response("{'Error':'does not exist'}",status = status.HTTP_400_BAD_REQUEST)


	def delete(self, request, pk=None):
		"""
		For deleting existing reports
		"""
		if 'pk' not in self.kwargs:
			return Response(
				status = status.HTTP_400_BAD_REQUEST
				)
		try:
			report = Report.objects.get(pk=self.kwargs['pk'])
			if report.owner == request.user:
				report.delete()
				return Response(
					status = status.HTTP_200_OK
					)
			else:
				return Response(
					{"Error":"User is not the owner of this report"},
					status = status.HTTP_400_BAD_REQUEST
					)
		except:
			return Response(
				{"Error":"This report does not exist."},
				status = status.HTTP_400_BAD_REQUEST
				)

def FolderView(views.APIView):

	serializer_class = FolderSerializer

	def post(self, request):
		serializer = self.serializer_class(data=request.data)
		if serializer.is_valid():
			serializer.save(owner=request.user)
			return Response(
				{"Message":"Folder successfully created"},
				status = status.HTTP_201_CREATED
				)


# Create your views here.
