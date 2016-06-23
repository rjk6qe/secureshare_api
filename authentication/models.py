from django.db import models
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token

class UserProfile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True,)
	site_manager = models.BooleanField(default=False)