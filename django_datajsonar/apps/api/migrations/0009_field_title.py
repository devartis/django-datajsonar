# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2017-10-12 13:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_auto_20171012_0849'),
    ]

    operations = [
        migrations.AddField(
            model_name='field',
            name='title',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
