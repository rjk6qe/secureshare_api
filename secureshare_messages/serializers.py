from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers

from secureshare_messages.models import Message
from authentication.models import UserProfile
from authentication.serializers import UserSerializer

from Crypto.PublicKey import RSA

class MessageSerializer(serializers.ModelSerializer):

	sender = UserSerializer(read_only=True)
	recipient = UserSerializer(read_only=True)

	class Meta:
		model = Message
		fields = ['sender','recipient','subject','body','encrypted','pk']

	def validate(self, data):
		subject = data.get('subject', None)
		body = data.get('body',None)
		if subject and body:
			return data
		else:
			raise serializers.ValidationError({"Error":"Missing fields"})

	def create(self, validated_data):
		sender = validated_data.get('sender',None)
		recipient = validated_data.get('recipient',None)
		subject = validated_data.get('subject',None)
		body = validated_data.get('body', None)
		encrypted = validated_data.get('encrypted', False)

		if encrypted:
			user_profile = UserProfile.objects.get(user=recipient)
			pub_key = RSA.importKey(user_profile.public_key)
			body = str(pub_key.encrypt(body.encode('utf-8'), 32)[0])
			subject = str(pub_key.encrypt(subject.encode('utf-8'), 32)[0])

		m = Message.objects.create(
			sender = sender,
			recipient = recipient, 
			subject = subject,
			body = body,
			encrypted = encrypted 
			)
		m.save()
		return m