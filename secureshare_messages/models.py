from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Message(models.Model):
	sender = models.ForeignKey(User, related_name='message_user')
	recipient = models.ForeignKey(User, related_name='message_target')
	subject = models.CharField(max_length=100)
	body = models.TextField()
	encrypted = models.BooleanField()