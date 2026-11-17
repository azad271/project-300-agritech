from django.urls import path
from .views import HarvestListingListView

urlpatterns = [
    path('harvests/', HarvestListingListView.as_view(), name='harvest-list'),
]