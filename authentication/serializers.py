from django.contrib.auth.models import User

from rest_framework import serializers

from rest_framework.authtoken.models import Token


class UserSerializer(serializers.ModelSerializer):

	class Meta:
		model = User
		fields = ('username','password')

	def validate(self, data):
		new_username = data.get('username',None)
		new_password = data.get('password',None)

		if len(User.objects.filter(username = new_username)) > 0:
			raise serializers.ValidationError("ERROR: user already exists")

		if new_password and new_username:
			return data
		else:
			raise serializers.ValidationError("ERROR: username or password field empty")

	def create(self, validated_data):
		new_username = validated_data.get('username',None)
		new_password = validated_data.get('password',None)

		if new_username and new_password:
			u = User.objects.create(username=new_username)
			u.set_password(new_password)
			u.save()
			Token.objects.create(user = u)
			return u

