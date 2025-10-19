# shop/models.py
from django.db import models

class Brand(models.Model):
    name = models.CharField(max_length=120, unique=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    # Local uploaded image (preferred by templates & uploader)
    image = models.ImageField(upload_to='products/', null=True, blank=True)

    # Optional remote image (fallback if no local upload)
    image_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name
