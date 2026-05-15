from django.db import models
from stockapp.models import Stock

# Create your models here.
class Sale(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    quantity_sold = models.IntegerField(default=0)
    unit_price = models.IntegerField(default=0)
    total_amount = models.IntegerField(default=0)
    date = models.DateField(auto_now_add=True)

    def

    def __str__(self):
        return f"{self.stock.product} - {self.quantity_sold} units sold at {self.sale_price} each"
