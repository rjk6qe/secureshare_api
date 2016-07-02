from django.contrib.auth.models import User, Group
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers
from rest_framework.authtoken.models import Token

from authentication.models import UserProfile

from Crypto.PublicKey import RSA

class UserSerializer(serializers.ModelSerializer):

	testing = True

	class Meta:
		model = User
		fields = ('username','password','email')
		extra_kwargs = {'password':{'write_only':True}}

	def validate(self, data):
		new_username = data.get('username',None)
		new_password = data.get('password',None)
		new_email = data.get('email',None)

		if (new_username and new_password and new_email) or (new_username and new_password and self.testing):
			try:
				User.objects.get(email = new_email)
				raise serializers.ValidationError("User with this email already exists")
			except ObjectDoesNotExist:
				return data
		else:
			raise serializers.ValidationError("Missing required fields.")

	def create(self, validated_data):
		new_username = validated_data.get('username',None)
		new_password = validated_data.get('password',None)
		new_email = validated_data.get('email', None)

		user = User.objects.create(username=new_username)
		user.set_password(new_password)
		user.save()
		return user

class UserProfileSerializer(serializers.ModelSerializer):

	user = UserSerializer(read_only=True)
	testing = True

	class Meta:
		model = UserProfile
		fields = ('user','site_manager')
		extra_kwargs = {'site_manager':{'read_only':True}}

	def create(self, validated_data):
		user = validated_data.get('user')
		user_profile = UserProfile.objects.create(user=user)
		user_profile.save()

		key = RSA.generate(2048)
		user_profile.public_key = key.publickey().exportKey('PEM')
		user_profile.save()
		# temp = tempfile.NamedTemporaryFile(delete=True)
		if not self.testing:
			try:
				email = EmailMessage(
					subject="SecureShare Registration Email <PRIVATE KEY ATTACHED>",
					body="Dear " + request.user.username + ",\nAttached is your private key. Store this in a safe place and do not delete it.\nThanks,\nSecureShare",
					to=[u.email,]
					)
				# temp.write(key.exportKey('PEM'))
				# temp.seek(0)
				email.attach(file_name, key.exportKey('PEM'), 'application/pdf')
			finally:
				email.send(fail_silently=False)
		file_name = user.username + '_private_key.pem'
		with open('/home/richard/secureshare/temp_keys/'+file_name, 'wb') as f:
			f.write(key.exportKey('PEM'))

		return user_profile

class SiteManagerSerializer(serializers.Serializer):

	creating = serializers.BooleanField()
	users = serializers.ListField(
		child = serializers.CharField(max_length=30)
		)

	def validate(self, data):
		user_list = data.get('users')

		new_user_list = []
		for user in user_list:
			try:
				user = User.objects.get(username=user)
				new_user_list.append(UserProfile.objects.get(user=user))
			except ObjectDoesNotExist:
				raise serializers.ValidationError(
					{"Error":"At least one user does not exist"}
					)

		data['users'] = new_user_list
		return data

	def create(self, validated_data):
		site_manager = validated_data.get('site_manager')
		active = validated_data.get('active')
		user_list = validated_data.get('users')

		return_list = []
		for user_profile in user_list:
			user = user_profile.user

			user_profile.site_manager = site_manager
			user.is_active = active
			
			user_profile.save()
			user.save()
			
			return_list.append(user.username)

		return return_list

class GroupSerializer(serializers.Serializer):

	name = serializers.CharField(max_length=80)
	users = serializers.ListField(
		child=serializers.CharField(max_length=30)
		)
	delete = serializers.BooleanField(required=False)

	def validate(self, data):
		group_name = data.get('name')
		action = self.context.get('action')

		if action == 'update':
			delete = data.get('delete',None)
			if delete == None:
				raise serializers.ValidationError("Missing required field 'delete'")

		try:
			Group.objects.get(name=group_name)
			if action == 'create':
				raise serializers.ValidationError("Error":"This group name already exists")
		except ObjectDoesNotExist:
			if action == 'update':
				raise serializers.ValidationError("Group name does not exist")

		user_list = data.get('users')
		new_user_list = []

		for username in user_list:
			try:
				new_user_list.append(User.objects.get(username=username))
			except ObjectDoesNotExist:
				raise serializers.ValidationError("At least one user does not exist")
		data['users'] = new_user_list
		return data

	def create(self, validated_data):
		owner = self.context.get('user')
		group_name = validated_data.get('name')
		user_list = validated_data.get('users')

		new_group = Group.objects.create(
			name=group_name
			)

		for user in user_list:
			user.groups.add(new_group)
			user.save()

		owner.groups.add(new_group)
		owner.save()

		return new_group

	def update(self, instance, validated_data):
		delete = validated_data.get('delete',False) #default to adding users to groups
		user_list = validated_data.get('users')

		for user in user_list:
			group_list = user.groups.all()
			if not delete:
				if instance not in group_list:
					user.groups.add(instance)
			else:
				if instance in group_list:
					user.groups.remove(instance)
			user.save()

		return instance

class TokenSerializer(serializers.ModelSerializer):
	class Meta:
		model = Token
		fields = ('key',)
		extra_kwargs = {'key':{'read_only':True}}
