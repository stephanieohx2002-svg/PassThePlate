from datetime import timedelta, time

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from foodrescue.models import Establishment, Organisation, FoodListing, Reservation


class ReservationWorkflowTests(TestCase):

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

        self.second_org_user = User.objects.create_user(
            username="organisation2_test@gmail.com",
            email="organisation2_test@gmail.com",
            password="testpassword123"
        )

        self.second_organisation = Organisation.objects.create(
            user=self.second_org_user,
            organisation_name="Second Charity",
            contact_number="92345678",
            address="789 Test Street",
            postal_code="111222",
            team_size=3,
            organisation_type="volunteer_group",
            general_location="east",
            description="Second test organisation",
            is_verified=True
        )

        self.food_listing = FoodListing.objects.create(
            establishment=self.establishment,
            name="Canned Tuna",
            category="packaged_food",
            allergens="Fish",
            weight_kg="7.50",
            quantity=20,
            expiry_date=timezone.localdate() + timedelta(days=30),
            pickup_location="123 Test Street",
            description="Sealed canned tuna",
            status=FoodListing.Status.AVAILABLE
        )

    def test_reservation_starts_as_pending(self):
        reservation = Reservation.objects.create(
            food_listing=self.food_listing,
            organisation=self.organisation,
            pickup_date=timezone.localdate() + timedelta(days=1),
            pickup_time=time(14, 0),
            message="Requesting pickup"
        )

        self.assertEqual(reservation.status, Reservation.Status.PENDING)

    def test_approval_changes_reservation_and_listing_status(self):
        reservation = Reservation.objects.create(
            food_listing=self.food_listing,
            organisation=self.organisation,
            pickup_date=timezone.localdate() + timedelta(days=1),
            pickup_time=time(14, 0),
            message="Requesting pickup"
        )

        self.client.login(
            username="establishment_test@gmail.com",
            password="testpassword123"
        )

        response = self.client.post(reverse("approve_reservation", args=[reservation.id]))

        reservation.refresh_from_db()
        self.food_listing.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(reservation.status, Reservation.Status.APPROVED)
        self.assertEqual(self.food_listing.status, FoodListing.Status.RESERVED)

    def test_approving_one_request_rejects_other_pending_requests(self):
        first_reservation = Reservation.objects.create(
            food_listing=self.food_listing,
            organisation=self.organisation,
            pickup_date=timezone.localdate() + timedelta(days=1),
            pickup_time=time(14, 0),
            message="First request"
        )

        second_reservation = Reservation.objects.create(
            food_listing=self.food_listing,
            organisation=self.second_organisation,
            pickup_date=timezone.localdate() + timedelta(days=1),
            pickup_time=time(15, 0),
            message="Second request"
        )

        self.client.login(
            username="establishment_test@gmail.com",
            password="testpassword123"
        )

        self.client.post(reverse("approve_reservation", args=[first_reservation.id]))

        first_reservation.refresh_from_db()
        second_reservation.refresh_from_db()

        self.assertEqual(first_reservation.status, Reservation.Status.APPROVED)
        self.assertEqual(second_reservation.status, Reservation.Status.REJECTED)

    def test_rejecting_reservation_keeps_listing_available(self):
        reservation = Reservation.objects.create(
            food_listing=self.food_listing,
            organisation=self.organisation,
            pickup_date=timezone.localdate() + timedelta(days=1),
            pickup_time=time(14, 0),
            message="Requesting pickup"
        )

        self.client.login(
            username="establishment_test@gmail.com",
            password="testpassword123"
        )

        self.client.post(reverse("reject_reservation", args=[reservation.id]))

        reservation.refresh_from_db()
        self.food_listing.refresh_from_db()

        self.assertEqual(reservation.status, Reservation.Status.REJECTED)
        self.assertEqual(self.food_listing.status, FoodListing.Status.AVAILABLE)

    def test_two_sided_completion_marks_reservation_collected_and_listing_completed(self):
        reservation = Reservation.objects.create(
            food_listing=self.food_listing,
            organisation=self.organisation,
            pickup_date=timezone.localdate() + timedelta(days=1),
            pickup_time=time(14, 0),
            message="Approved pickup",
            status=Reservation.Status.APPROVED
        )

        self.food_listing.status = FoodListing.Status.RESERVED
        self.food_listing.save()

        self.client.login(
            username="organisation_test@gmail.com",
            password="testpassword123"
        )
        self.client.post(reverse("organisation_mark_pickup_completed", args=[reservation.id]))

        reservation.refresh_from_db()
        self.food_listing.refresh_from_db()

        self.assertEqual(reservation.status, Reservation.Status.APPROVED)
        self.assertTrue(reservation.organisation_marked_completed)
        self.assertEqual(self.food_listing.status, FoodListing.Status.RESERVED)

        self.client.logout()

        self.client.login(
            username="establishment_test@gmail.com",
            password="testpassword123"
        )
        self.client.post(reverse("establishment_mark_pickup_completed", args=[reservation.id]))

        reservation.refresh_from_db()
        self.food_listing.refresh_from_db()

        self.assertEqual(reservation.status, Reservation.Status.COLLECTED)
        self.assertEqual(self.food_listing.status, FoodListing.Status.COMPLETED)