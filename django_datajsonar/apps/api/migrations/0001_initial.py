# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-04-05 13:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django_datajsonar.apps.api.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Catalog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=2000)),
                ('identifier', models.CharField(max_length=200, unique=True)),
                ('metadata', models.TextField()),
                ('updated', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Dataset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(max_length=200)),
                ('metadata', models.TextField()),
                ('indexable', models.BooleanField(default=False)),
                ('present', models.BooleanField(default=True)),
                ('updated', models.BooleanField(default=False)),
                ('catalog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.Catalog')),
            ],
        ),
        migrations.CreateModel(
            name='Distribution',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.CharField(max_length=200)),
                ('metadata', models.TextField()),
                ('download_url', models.URLField(max_length=1024)),
                ('updated', models.BooleanField(default=False)),
                ('data_file', models.FileField(blank=True, max_length=2000, upload_to=django_datajsonar.apps.api.models.filepath)),
                ('data_hash', models.CharField(default=b'', max_length=128)),
                ('last_updated', models.DateTimeField(blank=True, null=True)),
                ('indexable', models.BooleanField(default=False)),
                ('dataset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.Dataset')),
            ],
        ),
        migrations.CreateModel(
            name='Field',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metadata', models.TextField()),
                ('updated', models.BooleanField(default=False)),
                ('error', models.BooleanField(default=False)),
                ('distribution', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.Distribution')),
            ],
        ),
    ]
