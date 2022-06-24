from django.core.validators import MinValueValidator
from django.db import models


class Import(models.Model):
    date = models.DateTimeField()


class Offer(models.Model):
    # obj_id = models.UUIDField()
    obj_id = models.CharField(max_length=36)
    imp = models.ForeignKey('Import', on_delete=models.DO_NOTHING)
    name = models.TextField()
    price = models.IntegerField(validators=[MinValueValidator(0)])
    is_actual = models.BooleanField(default=True)
    parent = models.ForeignKey(
            'Category', 
            on_delete=models.SET_NULL, 
            related_name='children_offers', 
            null=True
        )

    class Meta:
        unique_together = [['obj_id', 'imp']]

    def __repr__(self):
        return f"Offer \"{self.name}\", {'actual' if self.is_actual else 'archived'}"


class Category(models.Model):
    # obj_id = models.UUIDField()
    obj_id = models.CharField(max_length=36)
    imp = models.ForeignKey('Import', on_delete=models.DO_NOTHING)
    name = models.TextField()
    offers_price = models.IntegerField(default=0)
    all_offers = models.IntegerField(default=0)
    is_actual = models.BooleanField(default=True)
    parent = models.ForeignKey(
            'self', 
            on_delete=models.SET_NULL, 
            related_name='children_categories', 
            null=True
        )

    class Meta:
        unique_together = [['obj_id', 'imp']]

    def __repr__(self):
        return f"Category \"{self.name}\", {'actual' if self.is_actual else 'archived'}"
