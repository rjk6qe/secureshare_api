# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('subject', models.CharField(max_length=100)),
                ('body', models.TextField()),
                ('recipient', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='message_target')),
                ('sender', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='message_user')),
            ],
        ),
    ]
