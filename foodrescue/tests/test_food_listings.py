from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from foodrescue.models import Establishment, Organisation, FoodListing


class FoodListingTests(TestCase):
    """
    Unit tests for the food listing workflow.

    These tests check whether verified establishments can create food
    listings, whether near-expiry listings are detected correctly, and
    whether organisation users only see available food listings when browsing.
    """
    def setUp(self):
        """
        Creates reusable verified establishment and organisation accounts
        for the food listing tests.

        Test data is created in Django's temporary test database, so it does
        not affect the main development database.
        """
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
        """
        Test that a verified establishment can create a food listing
        through the create food listing view.

        The test also checks that the created listing is linked to the
        authenticated establishment and starts with AVAILABLE status.
        """
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
        # A successful form submission should redirect the user.
        self.assertEqual(response.status_code, 302)

        listing = FoodListing.objects.get(name="Canned Baked Beans")

        # The listing should belong to the establishment that created it.
        self.assertEqual(listing.establishment, self.establishment)

        # New food listings should be available by default.
        self.assertEqual(listing.status, FoodListing.Status.AVAILABLE)

    def test_near_expiry_listing_returns_true(self):
        """
        Test that the is_near_expiry property returns True when a food
        listing expires within 30 days.
        """
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
        """
        Test that the organisation browse page only displays AVAILABLE
        food listings.

        Reserved food listings should not appear because they are no longer
        available for organisations to request.
        """
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

        # Available listings should be visible to organisations.
        self.assertContains(response, available_listing.name)

        # Reserved listings should not be shown on the browse page.
        self.assertNotContains(response, reserved_listing.name)