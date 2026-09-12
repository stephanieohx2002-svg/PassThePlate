from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from foodrescue.models import Establishment, Organisation


class RegistrationTests(TestCase):

    def test_establishment_is_unverified_by_default(self):
        user = User.objects.create_user(
            username="establishment_test@gmail.com",
            email="establishment_test@gmail.com",
            password="testpassword123"
        )

        establishment = Establishment.objects.create(
            user=user,
            business_name="Test Supermarket",
            contact_number="91234567",
            address="123 Test Street",
            postal_code="123456",
            general_location="west",
            business_type="supermarket",
            description="Test establishment"
        )

        self.assertFalse(establishment.is_verified)

    def test_organisation_is_unverified_by_default(self):
        user = User.objects.create_user(
            username="organisation_test@gmail.com",
            email="organisation_test@gmail.com",
            password="testpassword123"
        )

        organisation = Organisation.objects.create(
            user=user,
            organisation_name="Test Charity",
            contact_number="91234567",
            address="456 Test Street",
            postal_code="654321",
            team_size=5,
            organisation_type="volunteer_group",
            general_location="central",
            description="Test organisation"
        )

        self.assertFalse(organisation.is_verified)

    def test_establishment_password_mismatch_does_not_create_user(self):
        response = self.client.post(reverse("register_establishment"), {
            "email": "wrongpass_establishment@gmail.com",
            "password": "testpassword123",
            "password_confirm": "differentpassword123",
            "business_name": "Wrong Password Supermarket",
            "contact_number": "91234567",
            "address": "123 Test Street",
            "postal_code": "123456",
            "general_location": "west",
            "business_type": "supermarket",
            "description": "Test establishment"
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            User.objects.filter(username="wrongpass_establishment@gmail.com").exists()
        )
        self.assertContains(response, "Passwords do not match")