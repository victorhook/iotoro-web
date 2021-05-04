from django.contrib import admin

# Register your models here.
from protocol import models

admin.site.register(models.MessageDownStream)
admin.site.register(models.MessageUpStream)
