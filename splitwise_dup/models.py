from django.db import models

# Create your models here.

class Users(models.Model):
    user_name = models.CharField(max_length=100)
    img=models.CharField(max_length=200)
