from django.db import models

from accounts.models import User

class HarvestListing(models.Model):
    LISTING_TYPE = (
        ('READY_STOCK', 'Ready Stock'),
        ('PRE_HARVEST', 'Pre-Harvest Booking'),
    )
    farmer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    crop_name = models.CharField(max_length=100)
    listing_type = models.CharField(max_length=20, choices=LISTING_TYPE, default='READY_STOCK')
    total_quantity = models.FloatField(help_text="পরিমাণ (কেজি)")
    price_per_kg = models.FloatField(help_text="প্রতি কেজির দাম")
    expected_harvest_date = models.DateField(null=True, blank=True)
    
    # জিপিএস কোঅর্ডিনেট (SQLite ফ্রেন্ডলি)
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.crop_name} - {self.total_quantity} KG"
