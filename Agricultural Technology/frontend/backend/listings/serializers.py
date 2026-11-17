from rest_framework import serializers
from .models import HarvestListing


class HarvestListingSerializer(serializers.ModelSerializer):
    farmer_name = serializers.ReadOnlyField(source='farmer.full_name')
    distance_km = serializers.FloatField(read_only=True)

    class Meta:
        model = HarvestListing
        fields = [
            'id',
            'farmer',
            'farmer_name',
            'crop_name',
            'listing_type',
            'total_quantity',
            'price_per_kg',
            'expected_harvest_date',
            'latitude',
            'longitude',
            'created_at',
            'distance_km',
        ]
        read_only_fields = ['id', 'farmer', 'farmer_name', 'created_at']

    def validate_total_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_price_per_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate_latitude(self, value):
        if not -90 <= value <= 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_longitude(self, value):
        if not -180 <= value <= 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value