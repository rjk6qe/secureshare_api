from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User

from rest_framework import serializers
from rest_framework.parsers import MultiPartParser, JSONParser

from report.models import Report, Document


class DocumentSerializer(serializers.ModelSerializer):

	class Meta:
		model = Document
		fields = ['file','pk']

class ReportSerializer(serializers.ModelSerializer):
	#optional fields go here

	parsers = (MultiPartParser, JSONParser)

	name = serializers.CharField(required=False)
	short_description = serializers.CharField(required = False)
	long_description = serializers.CharField(required = False)
#	owner = serializers.CharField(max_length=30)

	files = DocumentSerializer(read_only=True,many=True)

	class Meta:
		model = Report
		fields = (
			'pk',
			'name',
			'private',
			'short_description',
			'long_description',
			'files'
			)

	def unique_report(self, user, report_name):
		report_query = Report.objects.filter(name=report_name)
		if report_query is None:
			return True
		for report in report_query:
			if report.owner == user:
				return False
		return True

	# def validate(self, data):
	# 	#user = data.get('owner',None)
	# 	report_name = data.get('name',None)
	# 	s_descr = data.get('short_description',None)
	# 	l_descr = data.get('long_description',None)
	# 	if report_name and s_descr and l_descr:
	# 			return data
	# 	else:
	# 		raise serializers.ValidationError(
	# 			{"Error":"Missing required fields"}
	# 			)

	def create(self, validated_data):
		user = validated_data.get('owner',None)
		if user is not None:
			r = Report.objects.create(
				name=validated_data.get('name',None),
				short_description = validated_data.get('short_description',None),
				long_description = validated_data.get('long_description',None),
				private = validated_data.get('private',False),
				owner = user
				)
			r.save()
			return r

	def update(self, instance, validated_data): 
	 	instance.name = validated_data.get('name',instance.name)
	 	instance.short_description = validated_data.get('short_description',instance.short_description)
	 	instance.long_description = validated_data.get('long_description',instance.long_description)
	 	instance.save()
	 	return instance


"""
class MessageSerializer(serializers.ModelSerializer):


	class Meta:
		model = Message
		fields = ('sender','recipient','header','body')


#	def validate(self, data):
"""
