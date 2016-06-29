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
				raise serializers.ValidationError("ERROR: User with this email already exists")
			except ObjectDoesNotExist:
				return data
		else:
			raise serializers.ValidationError({"Message":"Missing required fields."})


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


class GroupSerializer(serializers.Serializer):

	group_name = serializers.CharField(max_length=80)
	users = serializers.ListField(
		child=serializers.CharField(max_length=30)
		)

	def validate(self, data):
		user_list = data.get('users')

		for username in user_list:
			try:
				user = User.objects.get(username=username)
			except ObjectDoesNotExist:
				raise serializers.ValidationError({"Error":"At least one user does not exist"})
		return data

	def create(self, validated_data):
		owner = validated_data.get('owner')
		new_group = Group.objects.create(name=validated_data.get('group_name'))
		new_group.save()

		owner.groups.add(new_group)
		user_list = validated_data.get('users')

		for username in user_list:
			user = User.objects.get(username=username)
			user.groups.add(new_group)

		return new_group

	def update(self, instance, validated_data):
		delete = validated_data.get('delete',False) #default to adding users to groups

		user_list = validated_data.get('users')

		for username in user_list:
			user = User.objects.get(username=username)
			if not delete:
				if instance not in user.groups.all():
					user.groups.add(instance)
			else:
				if instance in user.groups.all():
					user.groups.remove(instance)
			user.save()

		return instance