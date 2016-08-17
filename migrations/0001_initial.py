# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DarisProject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cid', models.CharField(max_length=256, verbose_name=b'Project ID')),
                ('name', models.CharField(max_length=256, verbose_name=b'Project Name', blank=True)),
                ('token', models.TextField(max_length=256, verbose_name=b'Access Token')),
            ],
        ),
        migrations.CreateModel(
            name='DarisServer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=32, verbose_name=b'Nick name')),
                ('host', models.CharField(max_length=128, verbose_name=b'Server host')),
                ('port', models.PositiveIntegerField(default=443, verbose_name=b'Server port')),
                ('transport', models.CharField(default=b'https', max_length=6, verbose_name=b'Server transport', choices=[(b'https', b'HTTPS'), (b'http', b'HTTP')])),
            ],
        ),
        migrations.AddField(
            model_name='darisproject',
            name='server',
            field=models.ForeignKey(to='send_to_daris.DarisServer'),
        ),
    ]
