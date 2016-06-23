from django.db import models
from django.contrib.auth.models import User, Group
# Create your models here.

class Document(models.Model):
	file = models.FileField(upload_to='uploads/%Y/%m/%d/')

class Report(models.Model):
	name = models.CharField(max_length=200)
	short_description = models.CharField(max_length=350)
	long_description =  models.TextField()
	owner = models.ForeignKey(User)
	files = models.ManyToManyField(Document)

class Folders(models.Model):
	owner = models.ForeignKey(User)
	groups = models.ManyToManyField(Group)
	reports = models.ManyToManyField(Report)