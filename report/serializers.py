from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User

from rest_framework import serializers

from report.models import Report#, Message

class ReportSerializer(serializers.ModelSerializer):
	#optional fields go here

	name = serializers.CharField(required=False)
	short_description = serializers.CharField(required = False)
	long_description = serializers.CharField(required = False)
	owner = serializers.CharField(max_length=30)

	class Meta:
		model = Report
		fields = ('name','short_description','long_description','owner')

	def unique_report(self, user, report_name):
		report_query = Report.objects.filter(name=report_name)
		owner = User.objects.get(username = user)
		if report_query is None:
			return True
		for report in report_query:
			if report.owner == owner:
				return False
		return True

	def validate(self, data):
		username = data['owner']
		report_name = data['name']
		if not self.unique_report(username, report_name):
			raise serializers.ValidationError("ERROR: user already created a report with this name")
		return data

	def create(self, validated_data):
		username = validated_data.get('owner',None)
		if username is not None:
			owner_of_report = User.objects.get(username=username)

		if owner_of_report is not None:
			r = Report.objects.create(
				name=validated_data.get('name',None),
				short_description = validated_data.get('short_description',None),
				long_description = validated_data.get('long_description',None),
				owner = owner_of_report
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
