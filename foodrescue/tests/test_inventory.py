from datetime import timedelta, time

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from foodrescue.models import Establishment, Organisation, FoodListing, Reservation


class InventoryTests(TestCase):

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

        self.approved_listing = FoodListing.objects.create(
            establishment=self.establishment,
            name="Approved But Not Collected Rice",
            category="dry_goods",
            allergens="None stated",
            weight_kg="10.00",
            quantity=10,
            expiry_date=timezone.localdate() + timedelta(days=30),
            pickup_location="123 Test Street",
            description="Approved but not collected",
            status=FoodListing.Status.RESERVED
        )

        self.collected_listing = FoodListing.objects.create(
            establishment=self.establishment,
            name="Collected Canned Beans",
            category="packaged_food",
            allergens="None stated",
            weight_kg="8.00",
            quantity=20,
            expiry_date=timezone.localdate() + timedelta(days=30),
            pickup_location="123 Test Street",
            description="Collected listing",
            status=FoodListing.Status.COMPLETED
        )

        self.approved_reservation = Reservation.objects.create(
            food_listing=self.approved_listing,
            organisation=self.organisation,
            pickup_date=timezone.localdate() + timedelta(days=1),
            pickup_time=time(14, 0),
            message="Approved only",
            status=Reservation.Status.APPROVED
        )

        self.collected_reservation = Reservation.objects.create(
            food_listing=self.collected_listing,
            organisation=self.organisation,
            pickup_date=timezone.localdate() + timedelta(days=1),
            pickup_time=time(15, 0),
            message="Collected pickup",
            status=Reservation.Status.COLLECTED,
            organisation_marked_completed=True,
            establishment_marked_completed=True,
            completed_at=timezone.now()
        )

    def test_approved_reservation_does_not_appear_in_inventory(self):
        self.client.login(
            username="organisation_test@gmail.com",
            password="testpassword123"
        )

        response = self.client.get(reverse("organisation_inventory"))

        self.assertNotContains(response, "Approved But Not Collected Rice")

    def test_collected_reservation_appears_in_inventory(self):
        self.client.login(
            username="organisation_test@gmail.com",
            password="testpassword123"
        )

        response = self.client.get(reverse("organisation_inventory"))

        self.assertContains(response, "Collected Canned Beans")