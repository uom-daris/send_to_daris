# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def load_initial_data(apps, schema_editor):
    DarisServer = apps.get_model("send_to_daris", "DarisServer")
    if not DarisServer.objects.filter(name='VicNode Daris').exists():
        DarisServer(name='VicNode DaRIS', host='mediaflux.vicnode.org.au', port=443, transport='https').save()
#    if not DarisServer.objects.filter(name='Local Daris').exists():
#        DarisServer(name='Local DaRIS', host='localhost', port=8086, transport='http').save()


def unload_initial_data(apps, schema_editor):
    DarisServer = apps.get_model("stores", "DarisServer")
    DarisServer.objects.filter(name='VicNode Daris').delete()
    DarisServer.objects.filter(name='VicNode Daris').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('send_to_daris', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_data, reverse_code=unload_initial_data),
    ]
