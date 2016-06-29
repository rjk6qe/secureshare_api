from django.db import models
from django.contrib.auth.models import User

import datetime

from django.utils.timezone import utc

from rest_framework import exceptions
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication

class UserProfile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True,)
	site_manager = models.BooleanField(default=False)
	public_key = models.BinaryField()

# class ExpiringToken(TokenAuthentication):
# 	def authenticate_credentials(self, key):
# 		try:
# 			token = self.model.objects.get(key=key)
# 		except self.model.DoesNotExist:
# 			raise exceptions.AuthenticationFailed('Invalid token')

# 		if not token.user.is_active:
# 			raise exceptions.AuthenticationFailed('User inactive')

# 		utc_now = datetime.now()