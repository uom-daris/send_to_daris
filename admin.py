from django.contrib import admin
from django.apps import apps
from .config import SendToDaRISConfig
from .models import DarisServer
from .models import DarisProject
from django.contrib import admin

if apps.is_installed(SendToDaRISConfig.name):
    admin.site.register(DarisServer, admin.ModelAdmin)
    admin.site.register(DarisProject, admin.ModelAdmin)
