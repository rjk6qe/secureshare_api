from django.contrib.auth.models import User
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
		# Token.objects.create(user=user)
		return user