from django.db import models

class Module(models.Model):
    title = models.CharField(max_length=200)
    module_code = models.CharField(max_length=10)
