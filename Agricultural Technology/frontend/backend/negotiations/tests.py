from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from listings.models import HarvestListing
from .models import NegotiationBid


class NegotiationFlowTests(TestCase):
    def setUp(self):
        self.farmer = User.objects.create_user(
            phone_number='01700000011',
            password='test-password',
            full_name='Farmer One',
            role='FARMER',
        )
        self.other_farmer = User.objects.create_user(
            phone_number='01700000012',
            password='test-password',
            full_name='Farmer Two',
            role='FARMER',
        )
        self.buyer = User.objects.create_user(
            phone_number='01700000013',
            password='test-password',
            full_name='Buyer One',
            role='BUYER',
        )
        self.listing = HarvestListing.objects.create(
            farmer=self.farmer,
            crop_name='Potatoes',
            total_quantity=100,
            price_per_kg=30,
            latitude=23.82,
            longitude=90.41,
        )
        self.client = APIClient()

    def create_bid(self, **overrides):
        payload = {
            'listing_id': self.listing.id,
            'buyer_name': 'Local Shop',
            'buyer_phone': '01712345678',
            'offered_price_per_kg': 27,
            'requested_quantity': 25,
        }
        payload.update(overrides)
        return self.client.post('/api/negotiations/bid/', payload, format='json')

    def test_buyer_can_submit_valid_bid_and_farmer_can_accept_once(self):
        response = self.create_bid()
        self.assertEqual(response.status_code, 201)
        bid = NegotiationBid.objects.get(id=response.data['bid_id'])

        self.client.force_authenticate(user=self.farmer)
        offers = self.client.get('/api/negotiations/offers/')
        self.assertEqual(offers.status_code, 200)
        self.assertEqual(offers.data[0]['buyer_name'], 'Local Shop')

        decision = self.client.post(
            '/api/negotiations/offers/',
            {'bid_id': bid.id, 'action': 'ACCEPTED'},
            format='json',
        )
        self.assertEqual(decision.status_code, 200)
        bid.refresh_from_db()
        self.assertEqual(bid.status, NegotiationBid.Status.ACCEPTED)

        repeated_decision = self.client.post(
            '/api/negotiations/offers/',
            {'bid_id': bid.id, 'action': 'REJECTED'},
            format='json',
        )
        self.assertEqual(repeated_decision.status_code, 400)

    def test_bid_validates_quantity_and_offer(self):
        too_large = self.create_bid(requested_quantity=101)
        self.assertEqual(too_large.status_code, 400)
        free_offer = self.create_bid(offered_price_per_kg=0)
        self.assertEqual(free_offer.status_code, 400)

    def test_only_listing_farmer_can_view_and_decide_offers(self):
        bid_response = self.create_bid()
        bid_id = bid_response.data['bid_id']

        self.client.force_authenticate(user=self.buyer)
        self.assertEqual(self.client.get('/api/negotiations/offers/').status_code, 403)

        self.client.force_authenticate(user=self.other_farmer)
        self.assertEqual(self.client.get('/api/negotiations/offers/').data, [])
        denied = self.client.post(
            '/api/negotiations/offers/',
            {'bid_id': bid_id, 'action': 'ACCEPTED'},
            format='json',
        )
        self.assertEqual(denied.status_code, 404)

    def test_invalid_offer_decision_is_rejected(self):
        self.client.force_authenticate(user=self.farmer)
        response = self.client.post(
            '/api/negotiations/offers/',
            {'bid_id': 999, 'action': 'PENDING'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
