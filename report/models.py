from django.db import models
from django.contrib.auth.models import User, Group
# Create your models here.

class Document(models.Model):
	file = models.FileField(upload_to='uploads/%Y/%m/%d/')
	encrypted = models.BooleanField(default=False)

class Report(models.Model):
	name = models.CharField(max_length=50)
	short_description = models.CharField(max_length=350)
	long_description =  models.TextField()
	files = models.ManyToManyField(Document)

	owner = models.ForeignKey(User)
	private = models.BooleanField(default=False)

class Folder(models.Model):
	owner = models.ForeignKey(User)
	groups = models.ManyToManyField(Group)
	reports = models.ManyToManyField(Report)
	name = models.CharField(max_length=50)