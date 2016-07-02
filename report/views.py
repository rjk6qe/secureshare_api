from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import permissions, viewsets, status, views
from rest_framework.response import Response

from report.serializers import ReportSerializer, FolderSerializer
from report.models import Report, Document, Folder
from authentication.models import UserProfile

import json

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
		user = request.user
		user_profile = UserProfile.objects.get(user=user)

		if 'pk' in self.kwargs:
			pk = self.kwargs['pk']
			try:
				selected = Report.objects.get(pk=pk)
				if selected.owner == request.user or selected.private == False or user_profile.site_manager:
					return Response(
						self.serializer_class(selected).data,
						status=status.HTTP_200_OK
						)
				raise ObjectDoesNotExist
			except ObjectDoesNotExist:
				return Response(
					{"Message":"Message not visible to current user."},
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

	def patch(self, request, pk=None):
		"""
		For updating existing report fields
		NOTE: Delete files not implemented
		"""
		if 'pk' not in self.kwargs:
			return Response(
				{"Message":"Keep to specify key"},
				status = status.HTTP_405_METHOD_NOT_ALLOWED,
				)
		pk = self.kwargs['pk']
		try:
			report = Report.objects.get(pk=pk)
			if request.user != report.owner:
				return Response({"Error":"You cannot modify a different user's report"},status=status.HTTP_400_BAD_REQUEST)

			serializer = self.serializer_class(
				report,
				data=json.loads(request.data.get('data')),
				context={'creating':False,'current_name':report.name}
				)
			if serializer.is_valid():
				serializer.save()
				return Response(
					serializer.data,
					status=status.HTTP_200_OK
					)
			else:
				return Response(
					{"Error":serializer.errors},
					status = status.HTTP_400_BAD_REQUEST
					)
			raise ObjectDoesNotExist
		except ObjectDoesNotExist:
			return Response(
				{"Message":"This report cannot be edited by the user"},
				status = status.HTTP_400_BAD_REQUEST
				)

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
			raise ObjectDoesNotExist
		except ObjectDoesNotExist:
			return Response(
				{"Message":"User cannot delete this report"},
				status = status.HTTP_400_BAD_REQUEST
				)

	def post(self, request):
		"""
		For creating reports
		"""

		json_dict = json.loads(request.data.get('data'),None)
		if json_dict == None:
			return Response({"Error":"Missing 'data' field"},status=status.HTTP_400_BAD_REQUEST)
		

		file_list = request.FILES.getlist('file')
		num_files = len(file_list) or 0

		serializer = self.serializer_class(
			data = json_dict,
			context={'owner':request.user,'creating':True,'num_files':num_files}
			)

		if serializer.is_valid():
			report = serializer.save()
			if num_files > 0:
				encrypted_list = json_dict['encrypted']
				for i in range(0, num_files):
					new_doc = Document(file=file_list[i], encrypted=encrypted_list[i])
					new_doc.save()
					report.files.add(new_doc)
				report.save()
			return Response(
				self.serializer_class(report).data,
				status = status.HTTP_201_CREATED
				)
		else:
			return Response(
				{"Error":serializer.errors},
				status = status.HTTP_400_BAD_REQUEST
				)


class FolderView(views.APIView):

	serializer_class = FolderSerializer

	def get(self, request):
		queryset = Folder.objects.filter(owner=request.user)
		return Response(
			self.serializer_class(queryset,many=True),
			status = HTTP_200_OK
			)

	def post(self, request):
		serializer = self.serializer_class(
			data=request.data,
			context={'owner':request.user,'creating':True}
			)
		if serializer.is_valid():
			serializer.save()
			return Response(
				{"Message":"Folder successfully created"},
				status = status.HTTP_201_CREATED
				)
		else:
			return Response({"Error":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

	def patch(self, request, pk=None):
		if 'pk' not in self.kwargs:
			return Response(
				{"Message":"Must specify key to update folders"},
				status = status.HTTP_400_BAD_REQUEST
				)

		pk = self.kwargs['pk']
		try:
			folder = Folder.objects.get(pk=pk)
			if folder.owner == request.user:
				serializer = self.serializer_class(
					folder, 
					data=request.data, 
					context={'creating':False}
					)
				if serializer.is_valid():
					serializer.save()
				else:
					return Response(
						{"Error":serializer.errors},
						status = status.HTTP_400_BAD_REQUEST
						)
			raise ObjectDoesNotExist
		except ObjectDoesNotExist:
			return Response(
				{"Message":"User cannot access this folder"}
				)

	def delete(self, request,pk=None):
		if 'pk' not in self.kwargs:
			return Response(
				{"Message":"Must specify which folder to delete"},
				status = status.HTTP_400_BAD_REQUEST
				)
		pk = self.kwargs['pk']

		try:
			folder = Folder.objects.get(pk=pk)
			if folder.owner == request.user:
				folder.delete()
				return Response(
					{"Message":"Folder deleted successfully"},
					status=status.HTTP_200_OK
					)
			raise ObjectDoesNotExist
		except ObjectDoesNotExist:
			return Response(
				{"Message":"User cannot edit this folder"},
				status = status.HTTP_400_BAD_REQUEST
				)