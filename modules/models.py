from django.db import models

class Module(models.Model):
    title = models.CharField(max_length=200)
    module_code = models.CharField(max_length=10, primary_key=True)

    def __str__(self) -> str:
        return self.module_code + " " + self.title
