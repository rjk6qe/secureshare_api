from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Report(models.Model):
	name = models.CharField(max_length=200)
	short_description = models.CharField(max_length=350)
	long_description =  models.TextField()
	owner = models.ForeignKey(User)