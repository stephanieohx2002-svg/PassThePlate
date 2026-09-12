from django.conf import settings
from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone

class Establishment(models.Model):
    class Region(models.TextChoices):
        NORTH = "north", "North"
        EAST = "east", "East"
        SOUTH = "south", "South"
        WEST = "west", "West"
        CENTRAL = "central", "Central"

    class BusinessType(models.TextChoices):
        SUPERMARKET = "supermarket", "Supermarket"
        BAKERY = "bakery", "Bakery"
        WHOLESALER = "wholesaler", "Wholesaler"
        MANUFACTURER = "manufacturer", "Manufacturer"
        OTHER = "other", "Other"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="establishment_profile"
    )

    business_name = models.CharField(max_length=200)

    profile_image = models.ImageField(
        upload_to="establishment_profile_images/",
        blank=True,
        null=True
    )

    description = models.TextField(blank=True)

    address = models.TextField()

    postal_code = models.CharField(
        max_length=10,
        blank=True
    )

    general_location = models.CharField(
        max_length=20,
        choices=Region.choices,
        default=Region.WEST
    )

    business_type = models.CharField(
        max_length=30,
        choices=BusinessType.choices,
        blank=True
    )

    contact_number = models.CharField(max_length=30, blank=True)

    certification_file = models.FileField(
        upload_to="establishment_certifications/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])]
    )

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.business_name

class Organisation(models.Model):
    class GeneralLocation(models.TextChoices):
        NORTH = "north", "North"
        EAST = "east", "East"
        SOUTH = "south", "South"
        WEST = "west", "West"
        CENTRAL = "central", "Central"

    class OrganisationType(models.TextChoices):
        CERTIFIED_CHARITY = "certified_charity", "Certified Charity Organisation"
        VOLUNTEER_GROUP = "volunteer_group", "Volunteer Group"

    class ApplicationStatus(models.TextChoices):
        PENDING = "pending", "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organisation_profile"
    )

    organisation_name = models.CharField(max_length=200)

    profile_image = models.ImageField(
        upload_to="organisation_profile_images/",
        blank=True,
        null=True
    )

    description = models.TextField(blank=True)

    address = models.TextField(blank=True)

    postal_code = models.CharField(
        max_length=10,
        blank=True
    )

    contact_number = models.CharField(
        max_length=30,
        blank=True
    )

    team_size = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    organisation_type = models.CharField(
        max_length=30,
        choices=OrganisationType.choices,
        blank=True
    )

    general_location = models.CharField(
        max_length=20,
        choices=GeneralLocation.choices,
        blank=True
    )

    certification_file = models.FileField(
        upload_to="organisation_certifications/",
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=["pdf"])]
    )

    application_status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING
    )

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.organisation_name

class FoodListing(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        RESERVED = "reserved", "Reserved"
        COMPLETED = "completed", "Completed"
        EXPIRED = "expired", "Expired"

    class Category(models.TextChoices):
        BAKERY = "bakery", "Bakery"
        PACKAGED_FOOD = "packaged_food", "Packaged Food"
        DRY_GOODS = "dry_goods", "Dry Goods"
        FRESH_PRODUCE = "fresh_produce", "Fresh Produce"
        CHILLED = "chilled", "Chilled"
        FROZEN = "frozen", "Frozen"
        BEVERAGES = "beverages", "Beverages"
        OTHER = "other", "Other"

    establishment = models.ForeignKey(
        Establishment,
        on_delete=models.CASCADE,
        related_name="food_listings"
    )

    name = models.CharField(max_length=200)

    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.OTHER
    )

    image = models.ImageField(
        upload_to="food_listing_images/",
        blank=True,
        null=True
    )
    description = models.TextField(blank=True)
    allergens = models.CharField(max_length=255, blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE
    )

    weight_kg = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField()
    expiry_date = models.DateField()

    is_halal = models.BooleanField(default=False)
    pickup_location = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def days_until_expiry(self):
        return (self.expiry_date - timezone.localdate()).days

    @property
    def is_near_expiry(self):
        return 0 <= self.days_until_expiry <= 30

    def __str__(self):
        return self.name

class Reservation(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"
        COLLECTED = "collected", "Collected"

    food_listing = models.ForeignKey(
        FoodListing,
        on_delete=models.CASCADE,
        related_name="reservations"
    )

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="reservations"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )

    message = models.TextField(blank=True)

    pickup_date = models.DateField()
    pickup_time = models.TimeField()

    organisation_marked_completed = models.BooleanField(default=False)
    establishment_marked_completed = models.BooleanField(default=False)

    completed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.organisation} reserved {self.food_listing}"
    
class DistributionEvent(models.Model):
    class Area(models.TextChoices):
        NORTH = "north", "North"
        EAST = "east", "East"
        SOUTH = "south", "South"
        WEST = "west", "West"
        CENTRAL = "central", "Central"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="distribution_events"
    )

    thumbnail = models.ImageField(
        upload_to="event_thumbnails/",
        blank=True,
        null=True
    )

    name = models.CharField(max_length=200)
    area = models.CharField(max_length=20, choices=Area.choices)
    address = models.TextField()
    postal_code = models.CharField(max_length=10)
    description = models.TextField(blank=True)

    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(blank=True, null=True)

    remarks = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
class DistributionEventItem(models.Model):
    event = models.ForeignKey(
        DistributionEvent,
        on_delete=models.CASCADE,
        related_name="event_items"
    )

    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name="distribution_event_items"
    )

    quantity = models.PositiveIntegerField(default=1)

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("event", "reservation")

    def __str__(self):
        return f"{self.reservation.food_listing.name} for {self.event.name}"