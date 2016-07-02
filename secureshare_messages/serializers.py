from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

from rest_framework import serializers

from secureshare_messages.models import Message
from authentication.models import UserProfile
from authentication.serializers import UserSerializer

from Crypto.PublicKey import RSA

class MessageSerializer(serializers.ModelSerializer):

	sender = UserSerializer(read_only=True)
	recipient = serializers.CharField(max_length=30)

	class Meta:
		model = Message
		fields = ['sender','recipient','subject','body','encrypted','pk']

	def validate(self, data):
		subject = data.get('subject', None)
		body = data.get('body',None)
		recipient = data.get('recipient',None)

		if not (subject and body and recipient):
			raise serializers.ValidationError("Missing required fields")
		try:
			recipient = User.objects.get(username=recipient)
			recipient_profile = UserProfile.objects.get(user = recipient)
			if data.get('encrypted', False) != False:
				RSA.importKey(recipient_profile.public_key)
			data['recipient'] = recipient_profile
			return data
		except ObjectDoesNotExist:
			raise serializers.ValidationError("Recipient does not exist")
		except (IndexError, ValueError):
			raise serializers.ValidationError("Recipient does not have a valid public key")

	def create(self, validated_data):
		sender = validated_data.get('sender',None)
		recipient = validated_data.get('recipient',None)
		subject = validated_data.get('subject',None)
		body = validated_data.get('body', None)
		encrypted = validated_data.get('encrypted', False)

		if encrypted:
			pub_key = RSA.importKey(recipient.public_key)
			body = str(pub_key.encrypt(body.encode('utf-8'), 32)[0])
			subject = str(pub_key.encrypt(subject.encode('utf-8'), 32)[0])

		m = Message.objects.create(
			sender = sender,
			recipient = recipient.user, 
			subject = subject,
			body = body,
			encrypted = encrypted 
			)
		return m