# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-09-23 12:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_datajsonar', '0016_node_timezone'),
    ]

    operations = [
        migrations.AddField(
            model_name='catalog',
            name='issued',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='dataset',
            name='issued',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='distribution',
            name='issued',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='field',
            name='issued',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
