from django.db import models

# Create your models here.
class user_to_user_mapping(models.Model):
    user_to_user = models.CharField(max_length=100)


class users_to_group_mapping(models.Model):
    group_name = models.CharField(max_length=100)
    group_members = models.CharField(max_length=10000)
    count_of_users = models.IntegerField()


class amount_messages_user_to_user(models.Model):
    sender = models.CharField(max_length=100)
    receiver = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    message = models.CharField(max_length=1000)

class amount_messages_users_to_group(models.Model):
    sender = models.CharField(max_length=100)
    group_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    message = models.CharField(max_length=1000)
