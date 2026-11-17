from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from listings.models import HarvestListing
from .models import NegotiationBid


class CreateBidSerializer(serializers.ModelSerializer):
    listing_id = serializers.PrimaryKeyRelatedField(
        source='listing',
        queryset=HarvestListing.objects.all(),
    )

    class Meta:
        model = NegotiationBid
        fields = [
            'listing_id',
            'buyer_name',
            'buyer_phone',
            'offered_price_per_kg',
            'requested_quantity',
        ]

    def validate_buyer_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Buyer name is required.")
        return value

    def validate_buyer_phone(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Buyer phone is required.")
        return value

    def validate_offered_price_per_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError("Offer price must be greater than zero.")
        return value

    def validate(self, attrs):
        quantity = attrs['requested_quantity']
        if quantity <= 0:
            raise serializers.ValidationError(
                {"requested_quantity": "Requested quantity must be greater than zero."}
            )
        if quantity > attrs['listing'].total_quantity:
            raise serializers.ValidationError(
                {"requested_quantity": "Requested quantity exceeds the available listing quantity."}
            )
        return attrs


class CreateNegotiationBidView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CreateBidSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        bid = serializer.save()
        return Response(
            {"message": "Offer sent to the farmer.", "bid_id": bid.id},
            status=status.HTTP_201_CREATED,
        )


class FarmerOffersView(APIView):
    permission_classes = [IsAuthenticated]

    def _farmer_only(self, request):
        if request.user.role != 'FARMER':
            return Response(
                {"error": "Only farmer accounts can access negotiation offers."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    def get(self, request):
        permission_error = self._farmer_only(request)
        if permission_error:
            return permission_error

        bids = NegotiationBid.objects.filter(
            listing__farmer=request.user
        ).select_related('listing').order_by('-created_at')
        results = [
            {
                "id": bid.id,
                "crop_name": bid.listing.crop_name,
                "farmer_name": bid.listing.farmer.full_name,
                "buyer_name": bid.buyer_name,
                "buyer_phone": bid.buyer_phone,
                "original_price": bid.listing.price_per_kg,
                "offered_price": bid.offered_price_per_kg,
                "requested_quantity": bid.requested_quantity,
                "status": bid.status,
                "created_at": bid.created_at.strftime("%Y-%m-%d %H:%M"),
            }
            for bid in bids
        ]
        return Response(results)

    def post(self, request):
        permission_error = self._farmer_only(request)
        if permission_error:
            return permission_error

        bid_id = request.data.get('bid_id')
        action = request.data.get('action')
        if action not in (NegotiationBid.Status.ACCEPTED, NegotiationBid.Status.REJECTED):
            return Response(
                {"error": "Action must be ACCEPTED or REJECTED."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            bid = get_object_or_404(
                NegotiationBid.objects.select_for_update(),
                id=bid_id,
                listing__farmer=request.user,
            )
            if bid.status != NegotiationBid.Status.PENDING:
                return Response(
                    {"error": "This offer has already been resolved."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            bid.status = action
            bid.save(update_fields=['status'])

        return Response({"message": f"Offer {action.lower()}."})
