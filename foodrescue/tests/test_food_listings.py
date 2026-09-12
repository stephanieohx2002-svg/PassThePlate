from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from foodrescue.models import Establishment, Organisation, FoodListing


class FoodListingTests(TestCase):

    def setUp(self):
        self.establishment_user = User.objects.create_user(
            username="establishment_test@gmail.com",
            email="establishment_test@gmail.com",
            password="testpassword123"
        )

        self.establishment = Establishment.objects.create(
            user=self.establishment_user,
            business_name="Test Supermarket",
            contact_number="91234567",
            address="123 Test Street",
            postal_code="123456",
            general_location="west",
            business_type="supermarket",
            description="Test establishment",
            is_verified=True
        )

        self.organisation_user = User.objects.create_user(
            username="organisation_test@gmail.com",
            email="organisation_test@gmail.com",
            password="testpassword123"
        )

        self.organisation = Organisation.objects.create(
            user=self.organisation_user,
            organisation_name="Test Charity",
            contact_number="91234567",
            address="456 Test Street",
            postal_code="654321",
            team_size=5,
            organisation_type="volunteer_group",
            general_location="central",
            description="Test organisation",
            is_verified=True
        )

    def test_verified_establishment_can_create_food_listing(self):
        self.client.login(
            username="establishment_test@gmail.com",
            password="testpassword123"
        )

        response = self.client.post(reverse("create_food_listing"), {
            "name": "Canned Baked Beans",
            "category": "packaged_food",
            "allergens": "None stated",
            "weight_kg": "8.00",
            "quantity": "20",
            "expiry_date": (timezone.localdate() + timedelta(days=20)).isoformat(),
            "is_halal": "on",
            "pickup_location": "123 Test Street",
            "description": "Sealed canned food suitable for redistribution."
        })

        self.assertEqual(response.status_code, 302)

        listing = FoodListing.objects.get(name="Canned Baked Beans")
        self.assertEqual(listing.establishment, self.establishment)
        self.assertEqual(listing.status, FoodListing.Status.AVAILABLE)

    def test_near_expiry_listing_returns_true(self):
        listing = FoodListing.objects.create(
            establishment=self.establishment,
            name="Near Expiry Biscuits",
            category="packaged_food",
            allergens="Wheat",
            weight_kg="2.50",
            quantity=10,
            expiry_date=timezone.localdate() + timedelta(days=15),
            pickup_location="123 Test Street",
            description="Near expiry test listing",
            status=FoodListing.Status.AVAILABLE
        )

        self.assertTrue(listing.is_near_expiry)

    def test_browse_page_only_shows_available_listings(self):
        available_listing = FoodListing.objects.create(
            establishment=self.establishment,
            name="Available Rice",
            category="dry_goods",
            allergens="None stated",
            weight_kg="10.00",
            quantity=10,
            expiry_date=timezone.localdate() + timedelta(days=60),
            pickup_location="123 Test Street",
            description="Available test listing",
            status=FoodListing.Status.AVAILABLE
        )

        reserved_listing = FoodListing.objects.create(
            establishment=self.establishment,
            name="Reserved Pasta",
            category="dry_goods",
            allergens="Wheat",
            weight_kg="5.00",
            quantity=5,
            expiry_date=timezone.localdate() + timedelta(days=60),
            pickup_location="123 Test Street",
            description="Reserved test listing",
            status=FoodListing.Status.RESERVED
        )

        self.client.login(
            username="organisation_test@gmail.com",
            password="testpassword123"
        )

        response = self.client.get(reverse("browse_food_listings"))

        self.assertContains(response, available_listing.name)
        self.assertNotContains(response, reserved_listing.name)