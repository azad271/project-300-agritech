from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from .models import HarvestListing


class NearbyHarvestListingTests(TestCase):
    def setUp(self):
        farmer = User.objects.create_user(
            phone_number='01700000001',
            password='test-password',
            full_name='Local Farmer',
            role='FARMER',
        )
        self.listing = HarvestListing.objects.create(
            farmer=farmer,
            crop_name='Tomatoes',
            total_quantity=200,
            price_per_kg=30,
            latitude=23.82,
            longitude=90.41,
        )
        self.client = APIClient()

    def test_nearby_endpoint_returns_listing_with_distance(self):
        response = self.client.get(
            '/api/listings/nearby/',
            {'lat': 23.81, 'lng': 90.41, 'radius': 5},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.listing.id)
        self.assertGreaterEqual(response.data[0]['distance_km'], 0)

    def test_nearby_endpoint_rejects_invalid_coordinates_and_radius(self):
        for params in (
            {'lat': '91'},
            {'lng': '181'},
            {'radius': 'NaN'},
            {'radius': '-1'},
        ):
            with self.subTest(params=params):
                response = self.client.get('/api/listings/nearby/', params)
                self.assertEqual(response.status_code, 400)

    def test_only_authenticated_farmers_can_create_listings(self):
        payload = {
            'crop_name': 'Potatoes',
            'total_quantity': 50,
            'price_per_kg': 22,
            'latitude': 23.8,
            'longitude': 90.4,
        }
        response = self.client.post('/api/listings/create/', payload)
        self.assertEqual(response.status_code, 401)

        buyer = User.objects.create_user(
            phone_number='01700000002',
            password='test-password',
            full_name='Commercial Buyer',
            role='BUYER',
        )
        self.client.force_authenticate(user=buyer)
        response = self.client.post('/api/listings/create/', payload)
        self.assertEqual(response.status_code, 403)

        farmer = self.listing.farmer
        self.client.force_authenticate(user=farmer)
        response = self.client.post('/api/listings/create/', payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['farmer'], farmer.id)

    def test_listing_rejects_invalid_quantity_and_coordinates(self):
        self.client.force_authenticate(user=self.listing.farmer)
        for payload in (
            {'crop_name': 'Rice', 'total_quantity': 0, 'price_per_kg': 30, 'latitude': 23, 'longitude': 90},
            {'crop_name': 'Rice', 'total_quantity': 10, 'price_per_kg': 30, 'latitude': 91, 'longitude': 90},
        ):
            with self.subTest(payload=payload):
                response = self.client.post('/api/listings/create/', payload)
                self.assertEqual(response.status_code, 400)
