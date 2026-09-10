from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("food-listings/", views.browse_food_listings, name="browse_food_listings"),
    path("food-listings/<int:listing_id>/reserve/", views.reserve_food_listing, name="reserve_food_listing"),
    path("reservation-success/", views.reservation_success, name="reservation_success"),

    path("establishment/reservations/", views.establishment_reservations, name="establishment_reservations"),
    path("reservations/<int:reservation_id>/approve/", views.approve_reservation, name="approve_reservation"),
    path("reservations/<int:reservation_id>/reject/", views.reject_reservation, name="reject_reservation"),
    path("food-listings/create/", views.create_food_listing, name="create_food_listing"),
    path("organisation/dashboard/", views.organisation_dashboard, name="organisation_dashboard"),
    path("organisation/inventory/", views.organisation_inventory, name="organisation_inventory"),
    path("organisation/distribution_events/", views.organisation_distribution_events, name="organisation_distribution_events"),
    path("create-event/", views.create_event, name="create_event"),
     # AJAX FILTERS
    path(
        "organisation-inventory/filter/",
        views.filter_inventory,
        name="filter_inventory"
    ),

    path(
        "create-event/filter-inventory/",
        views.filter_event_inventory,
        name="filter_event_inventory"
    ),
    path(
    "organisation_inventory/<int:reservation_id>/details/",
    views.inventory_food_detail,
    name="inventory_food_detail"
),
    path(
    "events/<int:event_id>/",
    views.event_detail,
    name="event_detail"
),
    path(
    "food-listings/<int:listing_id>/details/",
    views.food_listing_detail,
    name="food_listing_detail"
),
    path(
    "inventory/<int:reservation_id>/update-quantity/",
    views.update_inventory_quantity,
    name="update_inventory_quantity"
),
    
    path("login/", views.login_view, name="login"),
path("logout/", views.logout_view, name="logout"),
path(
    "register/organisation/",
    views.register_organisation,
    name="register_organisation"
),
path(
    "register/submitted/",
    views.registration_submitted,
    name="registration_submitted"
),
path(
    "register/establishment/",
    views.register_establishment,
    name="register_establishment"
),
path("organisation/profile/", views.organisation_profile, name="organisation_profile"),
path("logout/", views.logout_view, name="logout"),
path("", views.public_home, name="public_home"),
path(
    "establishment/dashboard/",
    views.establishment_dashboard,
    name="establishment_dashboard"
),
path(
    "reservations/<int:reservation_id>/organisation-complete/",
    views.organisation_mark_pickup_completed,
    name="organisation_mark_pickup_completed"
),

path(
    "reservations/<int:reservation_id>/establishment-complete/",
    views.establishment_mark_pickup_completed,
    name="establishment_mark_pickup_completed"
),
path("logout/", views.logout_view, name="logout"),
path(
    "establishment/profile/",
    views.establishment_profile,
    name="establishment_profile"
),
path(
    "establishment/food-listings/",
    views.establishment_food_listings,
    name="establishment_food_listings"
),
path(
    "establishment/food-listings/<int:listing_id>/",
    views.establishment_food_listing_detail,
    name="establishment_food_listing_detail"
),
path("organisations/", views.public_organisations, name="public_organisations"),
path("organisations/<int:organisation_id>/", views.public_organisation_profile, name="public_organisation_profile"),
path("establishments/", views.public_establishments, name="public_establishments"),
path("establishments/<int:establishment_id>/", views.public_establishment_profile, name="public_establishment_profile"),
path("public_distribution_events/", views.public_distribution_events, name="public_distribution_events"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)