from django.contrib import admin
from .models import (
    Organisation,
    Establishment,
    FoodListing,
    Reservation,
    DistributionEvent,
    DistributionEventItem,
)

# Register core workflow models so administrators can inspect records in Django Admin.
admin.site.register(FoodListing)
admin.site.register(Reservation)
admin.site.register(DistributionEvent)
admin.site.register(DistributionEventItem)


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    """
    Determines how Organisation records are displayed in Django Admin.

    Administrators can review organisation details, filter applications,
    search for specific organisations, and update verification fields.
    """
    list_display = (
        "organisation_name",
        "user",
        "organisation_type",
        "general_location",
        "team_size",
        "contact_number",
        "application_status",
        "is_verified",
        "created_at",
    )

    list_filter = (
        "application_status",
        "is_verified",
        "organisation_type",
        "general_location",
    )

    search_fields = (
        "organisation_name",
        "user__username",
        "user__email",
        "contact_number",
        "address",
        "postal_code",
    )


@admin.register(Establishment)
class EstablishmentAdmin(admin.ModelAdmin):
    """
    Determines how Establishment records are displayed in Django Admin.

    Administrators can review establishment details, search for specific
    establishments, and update the is_verified field after checking submissions.
    """
    list_display = (
        "business_name",
        "user",
        "general_location",
        "contact_number",
        "is_verified",
        "created_at",
    )

    list_filter = (
        "is_verified",
        "general_location",
    )

    search_fields = (
        "business_name",
        "user__username",
        "user__email",
        "contact_number",
        "address",
    )