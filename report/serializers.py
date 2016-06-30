from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers
from rest_framework.parsers import MultiPartParser, JSONParser

from report.models import Report, Document, Folder


class DocumentSerializer(serializers.ModelSerializer):

	class Meta:
		model = Document
		fields = ['file','pk','encrypted']

class ReportSerializer(serializers.ModelSerializer):

	name = serializers.CharField(required=False)
	short_description = serializers.CharField(required = False)
	long_description = serializers.CharField(required = False)
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
		for report in report_query:
			if report.owner == user:
				return False
		return True

	def validate(self, data):
		creating = self.context.get('updating', True)
		owner = self.context.get('owner',None)

		if creating:
			report_name = data.get('name',None)
			s_descr = data.get('short_description',None)
			l_descr = data.get('long_description',None)
			data['owner'] = owner

			if not (report_name and s_descr and l_descr):
				raise serializers.ValidationError(
					{"Error":"Missing required fields"}
					)
			if not self.unique_report(owner, report_name):
				raise serializers.ValidationError(
					{"Error":"User already has a report with this name"}
					)
		return data

	def create(self, validated_data):
		r = Report.objects.create(
			name=validated_data.get('name',None),
			short_description = validated_data.get('short_description',None),
			long_description = validated_data.get('long_description',None),
			private = validated_data.get('private',False),
			owner = validated_data.get('owner',None)
			)
		return r

	def update(self, instance, validated_data): 
		instance.name = validated_data.get('name',instance.name)
		instance.short_description = validated_data.get('short_description',instance.short_description)
		instance.long_description = validated_data.get('long_description',instance.long_description)
		instance.save()
		return instance

class FolderSerializer(serializers.ModelSerializer):

	reports = serializers.ListField(
		child = serializers.CharField(max_length=50)
		)
	groups = serializers.ListField(
		child = serializers.CharField(max_length=80)
		)

	class Meta:
		model = Folder
		fields = ['name','reports','groups']

	def validate(self, data):
		creating = self.context.get('creating')

		if creating:
			owner = self.context.get('owner')
			data['owner'] = owner
			name = data.get('name')
			for folder in Folder.objects.filter(owner=owner):
				if folder.name == name:
					raise serializers.ValidationError(
						{"Error":"User already has a report with this name"}
						)

		report_list = data.get('reports')
		group_list = data.get('groups')
		new_report_list = []
		new_group_list = []

		r = Report()
		for report in report_list:
			try:
				new_report_list.append(Report.objects.get(name=report))
			except ObjectDoesNotExist:
				raise serializers.ValidationError(
					{"Error":"At least one report name was invalid"}
					)

		data['reports'] = new_report_list

		g = Group()
		for group in group_list:
			try:
				new_group_list.append(Group.objects.get(name=group))
			except ObjectDoesNotExist:
				raise serializers.ValidationError(
					{"Error":"At least one group name was invalid"}
					)

		data['groups'] = new_group_list

		return data

	def create(self, validated_data):
		report_list = validated_data.get('reports')
		group_list = validated_data.get('groups')
		name = validated_data.get('name')
		owner = validated_data.get('owner')

		folder = Folder.objects.create(
			name=name,
			owner=owner
			)

		for report in report_list:
			folder.reports.add(report)
		for group in group_list:
			folder.groups.add(group)

		folder.save()

		return folder

	def update(self, instance, validated_data):
		report_list = validated_data.get('reports')
		group_list = validated_data.get('groups')

		for report in instance.reports.all():
			instance.reports.remove(report)
		for group in instance.group.all():
			instance.groups.remove(group)

		for report in report_list:
			instance.reports.add(report)
		for group in group_list:
			instance.groups.add(group)

		instance.save()
		return instance