from django.contrib.auth.models import User

from rest_framework import serializers

from secureshare_messages.models import Message

class MessageSerializer(serializers.ModelSerializer):

	sender = serializers.CharField(max_length=30)
	recipient = serializers.CharField(max_length=30)


	class Meta:
		model = Message
		fields = ['sender','recipient','subject','body']

	def validate(self, data):
		recipient = data.get('recipient',None)
		subject = data.get('subject', None)
		body = data.get('body',None)
		if recipient and subject and body:
			num_rows = len(User.objects.filter(username=recipient))
			if num_rows < 1:
				raise serializers.ValidationError("ERROR: Recipient does not exist")
			else:
				return data
		else:
			raise serializers.ValidationError("ERROR: No recipient specified")


	def create(self, validated_data):
		sender_username = validated_data.get('sender',None)
		recipient_username = validated_data.get('recipient',None)
		subject = validated_data.get('subject',None)
		body = validated_data.get('body', None)

		sender = User.objects.get(username = sender_username)
		recipient = User.objects.get(username = recipient_username)
		m = Message.objects.create(
			sender = sender,
			recipient = recipient, 
			subject = subject,
			body = body )
		m.save()

		return m
