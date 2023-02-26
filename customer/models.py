from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# Create your models here.
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)



    def __str__(self):
        return self.user.username


