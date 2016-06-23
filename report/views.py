from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Q

from rest_framework import permissions, viewsets, status, views
from rest_framework.response import Response

from report.serializers import ReportSerializer#, MessageSerializer
from report.models import Report, Document#, Message

# class ReportViewSet(viewsets.ModelViewSet):
# 	"""
# 	works with:
# 	curl -H "Authorization: Token 8f9cd783fb5ee7261dd1ecd1de09fe4188fe129a" -F "file=@/home/richard/secureshare/secureshare/media/text/test.txt" -F "owner=richard" -F" name=files are fun2" -F "short_description=test" -F "long_description=testing" http://127.0.0.1:8000/api/v1/reports/

# 	Problem is the POST isn't JSON encoded, which seems bad
# 	"""
# 	serializer_class = ReportSerializer
# 	permission_classes = (permissions.AllowAny,)
	
# 	def get_queryset(self):
# 		pass

	
# 	def create(self, request):
# 		serializer = self.serializer_class(data = request.data)
# 		if serializer.is_valid():
# 			r = serializer.save()
# 			print(r.name)
# 			file_dict = request.FILES
# 			for filename in file_dict:
# 				print("found file")
# 				new_doc = Document(file = request.FILES[filename])
# 				new_doc.save()
# 				r.files.add(new_doc)
# 			return Response(serializer.validated_data)
# 		else:
# 			return Response(serializer.errors)
# 	"""
# 	def list(self, request):
# 		user = request.user
# 		queryset = Report.objects.filter(owner = user)
# 		serializer = ReportSerializer(queryset, many=True)
# 		return Response(serializer.data, status = status.HTTP_200_OK)
# 	"""

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
		if 'pk' in self.kwargs:
			return Response(self.kwargs['pk'])
		"""
		For listing data
		"""
		user = self.request.user
		if not user.is_anonymous():
			queryset = Report.objects.filter(Q(owner = user) | Q(private=False))
		else:
			return Response(status=status.HTTP_401_UNAUTHORIZED)
		return Response(self.serializer_class(queryset, many=True).data, status = status.HTTP_200_OK)

	def post(self, request):
		"""
		For creating reports
		"""
		serializer = self.serializer_class(data = request.data)
		if serializer.is_valid():
			if self.unique_report( request.user, serializer.validated_data['name'] ):
				r = serializer.save(owner=request.user)
				response_dict = {'key':r.pk}
				return Response(serializer.data, status = status.HTTP_201_CREATED)
			else:
				return Response({'Error':'User already created this report'},status = status.HTTP_400_BAD_REQUEST)
		else:
			return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)		

	def put(self, request):
		"""
		For uploading files for already existing reports
		"""
		pk = request.POST.get('report_number',None)
		try:
			report = Report.objects.get(pk=pk)

			if report.owner != request.user: #or has permission to do so
				return Response({"message":"does not have permission to modify this report"},status=status.HTTP_400_BAD_REQUEST)

			for filename in request.FILES.getlist('file'):
				new_doc = Document(file = filename)
				new_doc.save()
				report.files.add(new_doc)

			return Response(status = status.HTTP_202_ACCEPTED)

		except Content.DoesNotExist:
			return Response({"message":"code does not correspond to a valild report"},status = status.HTTP_400_BAD_REQUEST)

	def patch(self, request, pk=None):
		"""
		For updating existing reports
		"""
		


	def delete(self, request):
		"""
		For deleting existing reports
		"""

# Create your views here.
