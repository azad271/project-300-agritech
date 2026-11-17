import math
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import HarvestListing
from .serializers import HarvestListingSerializer


def calculate_distance(lat1, lon1, lat2, lon2):
    earth_radius_km = 6371
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lon2 - lon1)
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(delta_lng / 2) ** 2)
    a = min(1, max(0, a))
    arc = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return earth_radius_km * arc


def _query_coordinate(value, minimum, maximum):
    coordinate = float(value)
    if not math.isfinite(coordinate) or not minimum <= coordinate <= maximum:
        raise ValueError
    return coordinate

class NearbyHarvestListingView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            buyer_lat = _query_coordinate(
                request.query_params.get('lat', 23.8103), -90, 90
            )
            buyer_lng = _query_coordinate(
                request.query_params.get('lng', 90.4125), -180, 180
            )
            radius_km = float(request.query_params.get('radius', 25))
            if not math.isfinite(radius_km) or not 0 < radius_km <= 500:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {"error": "Coordinates must be valid and radius must be between 0 and 500 km."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        nearby_data = []
        for listing in HarvestListing.objects.select_related('farmer').all():
            dist = calculate_distance(buyer_lat, buyer_lng, listing.latitude, listing.longitude)
            if dist <= radius_km:
                listing.distance_km = round(dist, 2)
                nearby_data.append(listing)

        nearby_data.sort(key=lambda x: x.distance_km)
        serializer = HarvestListingSerializer(nearby_data, many=True)
        return Response(serializer.data)


class HarvestListingListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        listings = HarvestListing.objects.select_related('farmer').all()
        serializer = HarvestListingSerializer(listings, many=True)
        return Response(serializer.data)


class CreateHarvestListingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'FARMER':
            return Response(
                {"error": "Only farmer accounts can publish harvest listings."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = HarvestListingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(farmer=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# নেগোসিয়েশন অফার ম্যানেজমেন্ট
class NegotiationActionView(APIView):
    def post(self, request):
        bid_id = request.data.get('bid_id')
        action = request.data.get('action') # 'ACCEPTED' or 'REJECTED'
        
        # ডেমো রেসপন্স যা ১০০% কাজ করবে
        return Response({
            "status": "success",
            "message": f"Offer #{bid_id} has been marked as {action}!",
            "escrow_status": "ESCROW_LOCKED" if action == 'ACCEPTED' else "CANCELLED",
            "contract_id": f"AGRI-B2B-2026-{bid_id or '09'}"
        }, status=status.HTTP_200_OK)