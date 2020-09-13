from django.db import models

# Create your models here.
class user_to_user_mapping(models.Model):
    user1 = models.IntegerField()
    user2 = models.IntegerField()


class users_to_group_mapping(models.Model):
    group_id = models.IntegerField()
    user_id = models.IntegerField()


class group_members_count(models.Model):
    group_id = models.IntegerField()
    count_of_users = models.IntegerField()


class amount_messages_user_to_user(models.Model):
    sender = models.IntegerField()
    receiver = models.IntegerField()
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    message = models.CharField(max_length=1000)

class amount_messages_users_to_group(models.Model):
    sender = models.IntegerField()
    group_id = models.IntegerField()
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    message = models.CharField(max_length=1000)


class group_name_group_id(models.Model):
    group_name = models.CharField(max_length=100)
