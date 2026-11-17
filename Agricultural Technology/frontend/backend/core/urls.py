"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views.
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import RegisterView, UserTokenObtainPairView
from listings.views import (
    CreateHarvestListingView,
    HarvestListingListView,
    NearbyHarvestListingView,
)
from negotiations.views import CreateNegotiationBidView, FarmerOffersView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/', UserTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/harvests/', HarvestListingListView.as_view(), name='harvest-list'),
    path('api/listings/', include('listings.urls')),
    path('api/listings/nearby/', NearbyHarvestListingView.as_view(), name='nearby-listings'),
    path('api/listings/create/', CreateHarvestListingView.as_view(), name='create-listing'),
    path('api/negotiations/bid/', CreateNegotiationBidView.as_view(), name='create-bid'),
    path('api/negotiations/offers/', FarmerOffersView.as_view(), name='farmer-offers'),
]
from listings.views import NegotiationActionView

# urlpatterns এর ভেতরে যোগ করুন:
path('api/negotiations/action/', NegotiationActionView.as_view(), name='negotiation-action'),