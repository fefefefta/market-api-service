from django.db import models


class Offer(models.Model):
    id = models.UUIDField()
    date = models.DateTimeField(null=False)
    name = models.CharField(null=False)
    price = models.IntegerField(null=False)
    is_actual = models.BooleanField(null=False)
    parent = models.ForeignKey(
            'Category', 
            on_delete=models.CASCADE, 
            related_name='children', 
            null=True
        )


class Category(models.Model):
    id = models.UUIDField()
    date = models.DateTimeField(null=False)
    name = models.CharField(null=False)
    offers_price = models.IntegerField(null=True)
    all_offers = models.IntegerField(null=True)
    is_actual = models.BooleanField(null=False)
    parent = models.ForeignKey(
            'self', 
            on_delete=models.CASCADE, 
            related_name='children', 
            null=True
        )
