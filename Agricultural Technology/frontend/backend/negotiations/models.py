from django.db import models
from listings.models import HarvestListing


class NegotiationBid(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'

    listing = models.ForeignKey(
        HarvestListing,
        on_delete=models.CASCADE,
        related_name='bids',
    )
    buyer_name = models.CharField(max_length=100)
    buyer_phone = models.CharField(max_length=20)
    offered_price_per_kg = models.FloatField()
    requested_quantity = models.FloatField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bid by {self.buyer_name} for {self.listing.crop_name}"
