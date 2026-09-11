from django.shortcuts import render, get_object_or_404, redirect
from .models import (
    FoodListing,
    Reservation,
    Organisation,
    DistributionEvent,
    DistributionEventItem,
    Establishment,
)

from .forms import ReservationForm, FoodListingForm
from django.db import transaction

from django.http import JsonResponse
from django.template.loader import render_to_string

from django.db.models import Sum, Q, Count, Prefetch
import json

from django.views.decorators.http import require_POST

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.contrib.auth.models import User

from django.utils import timezone

from .decorators import organisation_required, establishment_required

@organisation_required
def browse_food_listings(request):

    selected_category = request.GET.get("category", "")
    halal_only = request.GET.get("halal") == "true"
    sort_by = request.GET.get("sort", "newest")
    search_query = request.GET.get("q", "").strip()

    listings = FoodListing.objects.filter(
        status=FoodListing.Status.AVAILABLE
    ).select_related("establishment")

    if selected_category:
        listings = listings.filter(category=selected_category)

    if halal_only:
        listings = listings.filter(is_halal=True)

    if search_query:
        listings = listings.filter(
            Q(name__icontains=search_query) |
            Q(establishment__business_name__icontains=search_query)
        )

    if sort_by == "oldest":
        listings = listings.order_by("created_at")
    else:
        listings = listings.order_by("-created_at")

    return render(request, "foodrescue/organisation-pages/browse_food_listings.html", {
        "listings": listings,
        "categories": FoodListing.Category.choices,
        "selected_category": selected_category,
        "halal_only": halal_only,
        "sort_by": sort_by,
        "search_query": search_query,
    })


@organisation_required
def reserve_food_listing(request, listing_id):

    organisation = request.user.organisation_profile

    food_listing = get_object_or_404(
        FoodListing,
        id=listing_id,
        status=FoodListing.Status.AVAILABLE
    )

    if request.method == "POST":
        form = ReservationForm(request.POST)

        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.food_listing = food_listing
            reservation.organisation = organisation
            reservation.status = Reservation.Status.PENDING
            reservation.save()

            return redirect("reservation_success")

    else:
        form = ReservationForm()

    return render(request, "foodrescue/organisation-pages/reserve_food_listing.html", {
        "form": form,
        "food_listing": food_listing
    })

def reservation_success(request):
    return render(request, "foodrescue/organisation-pages/reservation_success.html")

@establishment_required
def establishment_reservations(request):

    establishment = request.user.establishment_profile

    if not establishment.is_verified:
        return render(
            request,
            "foodrescue/access-denied.html",
            status=403
        )

    reservations = Reservation.objects.select_related(
        "food_listing",
        "food_listing__establishment",
        "organisation"
    ).filter(
        food_listing__establishment=establishment,
        status=Reservation.Status.PENDING
    ).order_by("-created_at")

    return render(
        request,
        "foodrescue/establishment-pages/establishment_reservations.html",
        {
            "reservations": reservations
        }
    )


@establishment_required
@require_POST
@transaction.atomic
def approve_reservation(request, reservation_id):
    establishment = request.user.establishment_profile

    reservation = get_object_or_404(
        Reservation.objects.select_related(
            "food_listing",
            "food_listing__establishment",
            "organisation"
        ),
        id=reservation_id,
        status=Reservation.Status.PENDING,
        food_listing__establishment=establishment
    )

    reservation.status = Reservation.Status.APPROVED
    reservation.save()

    food_listing = reservation.food_listing
    food_listing.status = FoodListing.Status.RESERVED
    food_listing.save()

    Reservation.objects.filter(
        food_listing=food_listing,
        status=Reservation.Status.PENDING
    ).exclude(
        id=reservation.id
    ).update(
        status=Reservation.Status.REJECTED
    )

    return redirect("establishment_dashboard")

@establishment_required
@require_POST
def reject_reservation(request, reservation_id):

    establishment = request.user.establishment_profile

    reservation = get_object_or_404(
        Reservation.objects.select_related(
            "food_listing",
            "food_listing__establishment",
            "organisation"
        ),
        id=reservation_id,
        status=Reservation.Status.PENDING,
        food_listing__establishment=establishment
    )

    reservation.status = Reservation.Status.REJECTED
    reservation.save()

    return redirect("establishment_dashboard")

@establishment_required
def create_food_listing(request):

    establishment = request.user.establishment_profile

    if request.method == "POST":
        form = FoodListingForm(request.POST, request.FILES)

        if form.is_valid():
            food_listing = form.save(commit=False)
            food_listing.establishment = establishment
            food_listing.status = FoodListing.Status.AVAILABLE
            food_listing.save()

            return redirect("establishment_dashboard")
    else:
        form = FoodListingForm()

    return render(request, "foodrescue/establishment-pages/create_food_listing.html", {
        "form": form,
    })
@organisation_required
def organisation_dashboard(request):
    organisation = request.user.organisation_profile

    selected_status = request.GET.get("status", "")

    reservations = Reservation.objects.select_related(
        "food_listing",
        "food_listing__establishment",
        "organisation"
    ).filter(
        organisation=organisation
    ).order_by("-created_at")

    if selected_status:
        reservations = reservations.filter(status=selected_status)

    accepted_pickups = Reservation.objects.select_related(
        "food_listing",
        "food_listing__establishment",
        "organisation"
    ).filter(
        organisation=organisation,
        status=Reservation.Status.APPROVED
    ).order_by("pickup_date", "pickup_time")

    completed_pickups = Reservation.objects.filter(
        organisation=organisation,
        status=Reservation.Status.COLLECTED
    ).count()

    total_food_rescued = Reservation.objects.filter(
        organisation=organisation,
        status=Reservation.Status.COLLECTED
    ).aggregate(
        total=Sum("food_listing__weight_kg")
    )["total"] or 0

    pending_requests = Reservation.objects.filter(
        organisation=organisation,
        status=Reservation.Status.PENDING
    ).count()

    return render(request, "foodrescue/organisation-pages/organisation_dashboard.html", {
        "organisation": organisation,
        "reservations": reservations,
        "accepted_pickups": accepted_pickups,
        "selected_status": selected_status,
        "completed_pickups": completed_pickups,
        "total_food_rescued": total_food_rescued,
        "pending_requests": pending_requests,
    })
    
@organisation_required
def organisation_inventory(request):

    organisation = request.user.organisation_profile

    selected_category = request.GET.get("category", "")
    halal_only = request.GET.get("halal") == "true"

    accepted_reservations = get_accepted_inventory(
        organisation,
        selected_category,
        halal_only
    )

    return render(request, "foodrescue/organisation-pages/organisation_inventory.html", {
        "accepted_reservations": accepted_reservations,
        "categories": FoodListing.Category.choices,
        "selected_category": selected_category,
        "halal_only": halal_only,
    })

def attach_remaining_quantities(reservations):
    for reservation in reservations:
        base_quantity = reservation.food_listing.quantity

        used_quantity = reservation.distribution_event_items.aggregate(
            total=Sum("quantity")
        )["total"] or 0

        reservation.remaining_quantity = max(
            int(base_quantity) - int(used_quantity),
            0
        )

    return reservations


def get_accepted_inventory(organisation, selected_category="", halal_only=False):
    accepted_reservations = Reservation.objects.select_related(
        "food_listing",
        "food_listing__establishment",
        "organisation"
    ).filter(
        organisation=organisation,
        status=Reservation.Status.APPROVED
    ).order_by("food_listing__expiry_date")

    if selected_category:
        accepted_reservations = accepted_reservations.filter(
            food_listing__category=selected_category
        )

    if halal_only:
        accepted_reservations = accepted_reservations.filter(
            food_listing__is_halal=True
        )

    accepted_reservations = attach_remaining_quantities(accepted_reservations)

    accepted_reservations = [
        reservation
        for reservation in accepted_reservations
        if reservation.remaining_quantity > 0
    ]

    return accepted_reservations

@organisation_required
def create_event(request):

    organisation = request.user.organisation_profile

    if request.method == "POST":
        event = DistributionEvent.objects.create(
            organisation=organisation,
            thumbnail=request.FILES.get("event_thumbnail"),
            name=request.POST.get("event_name"),
            area=request.POST.get("region"),
            address=request.POST.get("address"),
            postal_code=request.POST.get("postal_code"),
            description=request.POST.get("description"),
            event_date=request.POST.get("event_date"),
            start_time=request.POST.get("event_time"),
            end_time=request.POST.get("end_time") or None,
            remarks=request.POST.get("remarks", ""),
            status=DistributionEvent.Status.PUBLISHED,
        )

        selected_items_json = request.POST.get("selected_event_items", "[]")

        try:
            selected_items = json.loads(selected_items_json)
        except json.JSONDecodeError:
            selected_items = []

        for item in selected_items:
            reservation_id = item.get("reservation_id")
            quantity = int(item.get("quantity", 0))

            reservation = get_object_or_404(
                Reservation,
                id=reservation_id,
                organisation=organisation,
                status=Reservation.Status.APPROVED
            )

            base_quantity = reservation.food_listing.quantity

            used_quantity = reservation.distribution_event_items.aggregate(
                total=Sum("quantity")
            )["total"] or 0

            remaining_quantity = max(
                int(base_quantity) - int(used_quantity),
                0
            )

            if quantity > remaining_quantity:
                quantity = remaining_quantity

            if quantity > 0:
                DistributionEventItem.objects.create(
                    event=event,
                    reservation=reservation,
                    quantity=quantity
                )

        return redirect("organisation_distribution_events")

    selected_category = request.GET.get("category", "")
    halal_only = request.GET.get("halal") == "true"

    accepted_reservations = get_accepted_inventory(
        organisation,
        selected_category,
        halal_only
    )

    return render(request, "foodrescue/organisation-pages/create-event.html", {
        "accepted_reservations": accepted_reservations,
        "categories": FoodListing.Category.choices,
        "selected_category": selected_category,
        "halal_only": halal_only,
    })
    
@organisation_required
def filter_inventory(request):

    organisation = request.user.organisation_profile

    selected_category = request.GET.get("category", "")
    halal_only = request.GET.get("halal") == "true"

    accepted_reservations = get_accepted_inventory(
        organisation,
        selected_category,
        halal_only
    )

    html = render_to_string(
        "foodrescue/organisation-pages/partials/inventory-cards.html",
        {
            "accepted_reservations": accepted_reservations,
        },
        request=request
    )

    return JsonResponse({
        "html": html
    })

@organisation_required
def filter_event_inventory(request):

    organisation = request.user.organisation_profile

    selected_category = request.GET.get("category", "")
    halal_only = request.GET.get("halal") == "true"

    accepted_reservations = get_accepted_inventory(
        organisation,
        selected_category,
        halal_only
    )

    html = render_to_string(
        "foodrescue/organisation-pages/partials/inventory-add-cards.html",
        {
            "accepted_reservations": accepted_reservations,
        },
        request=request
    )

    return JsonResponse({
        "html": html
    })

@organisation_required
def inventory_food_detail(request, reservation_id):

    organisation = request.user.organisation_profile

    reservation = get_object_or_404(
        Reservation.objects.select_related(
            "food_listing",
            "food_listing__establishment",
            "organisation"
        ),
        id=reservation_id,
        organisation=organisation,
        status=Reservation.Status.APPROVED
    )

    return render(request, "foodrescue/organisation-pages/inventory-food-detail.html", {
        "reservation": reservation,
        "food_listing": reservation.food_listing,
    })
    
@organisation_required
def organisation_distribution_events(request):
    
    organisation = request.user.organisation_profile

    events = DistributionEvent.objects.select_related(
        "organisation"
    ).prefetch_related(
        "event_items__reservation__food_listing",
        "event_items__reservation__food_listing__establishment"
    ).filter(
        organisation=organisation
    ).order_by("event_date", "start_time")

    return render(request, "foodrescue/organisation-pages/organisation-distribution-events.html", {
        "events": events,
    })

def event_detail(request, event_id):
    event = get_object_or_404(
        DistributionEvent.objects.select_related(
            "organisation"
        ).prefetch_related(
            "event_items__reservation__food_listing",
            "event_items__reservation__food_listing__establishment"
        ),
        id=event_id
    )

    return render(request, "foodrescue/public-pages/event-detail.html", {
        "event": event,
    })
    
def food_listing_detail(request, listing_id):
    food_listing = get_object_or_404(
        FoodListing.objects.select_related("establishment"),
        id=listing_id
    )

    return render(request, "foodrescue/public-pages/food-listing-detail.html", {
        "food_listing": food_listing,
    })
    
@organisation_required
@require_POST
def update_inventory_quantity(request, reservation_id):

    organisation = request.user.organisation_profile

    if not organisation.is_verified:
        return JsonResponse(
            {"success": False, "error": "Account not verified."},
            status=403
        )

    reservation = get_object_or_404(
        Reservation.objects.select_related("food_listing"),
        id=reservation_id,
        organisation=organisation,
        status=Reservation.Status.APPROVED
    )

    action = request.POST.get("action")

    food_listing = reservation.food_listing

    used_quantity = reservation.distribution_event_items.aggregate(
        total=Sum("quantity")
    )["total"] or 0

    current_quantity = int(food_listing.quantity)

    if action == "increase":
        food_listing.quantity = current_quantity + 1

    elif action == "decrease":
        if current_quantity > used_quantity:
            food_listing.quantity = current_quantity - 1

    food_listing.save()

    remaining_quantity = (
        int(food_listing.quantity) - int(used_quantity)
    )

    return JsonResponse({
        "success": True,
        "remaining_quantity": remaining_quantity
    })
    
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip().lower()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            if hasattr(user, "organisation_profile"):
                if not user.organisation_profile.is_verified:
                    return render(
                        request,
                        "foodrescue/public-pages/login.html",
                        {
                            "error_message":
                            "Your organisation account is still awaiting verification."
                        }
                    )

                login(request, user)
                return redirect("organisation_dashboard")

            if hasattr(user, "establishment_profile"):
                if not user.establishment_profile.is_verified:
                    return render(
                        request,
                        "foodrescue/public-pages/login.html",
                        {
                            "error_message":
                            "Your establishment account is still awaiting verification."
                        }
                    )

                login(request, user)
                return redirect("establishment_dashboard")

            login(request, user)
            return redirect("public_distribution_events")

        return render(
            request,
            "foodrescue/public-pages/login.html",
            {
                "error_message": "Invalid email or password."
            }
        )

    return render(request, "foodrescue/public-pages/login.html")

@transaction.atomic
def register_organisation(request):
    if request.method == "POST":
        print(request.POST)  # temporary debug line

        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        organisation_name = request.POST.get("organisation_name", "").strip()
        contact_number = request.POST.get("contact_number", "").strip()
        address = request.POST.get("address", "").strip()
        postal_code = request.POST.get("postal_code", "").strip()
        team_size = request.POST.get("team_size") or None

        general_location = (
            request.POST.get("general_location")
        )

        organisation_type = (
            request.POST.get("organisation_type")
        )

        description = (
            request.POST.get("description")
        )

        profile_image = request.FILES.get("profile_image")
        certification_file = request.FILES.get("certification_file")

        if password != password_confirm:
            return render(request, "foodrescue/public-pages/register-organisation.html", {
                "error_message": "Passwords do not match."
            })

        if not organisation_type:
            return render(request, "foodrescue/public-pages/register-organisation.html", {
                "error_message": "Please select an organisation type."
            })

        if not general_location:
            return render(request, "foodrescue/public-pages/register-organisation.html", {
                "error_message": "Please select a region."
            })

        if User.objects.filter(username=email).exists():
            return render(request, "foodrescue/public-pages/register-organisation.html", {
                "error_message": "An account with this email already exists."
            })

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        Organisation.objects.create(
            user=user,
            organisation_name=organisation_name,
            contact_number=contact_number,
            address=address,
            postal_code=postal_code,
            team_size=team_size,
            general_location=general_location,
            organisation_type=organisation_type,
            description=description,
            profile_image=profile_image,
            certification_file=certification_file,
            is_verified=False
        )

        return redirect("registration_submitted")

    return render(request, "foodrescue/public-pages/register-organisation.html")

def registration_submitted(request):
    return render(request, "foodrescue/public-pages/registration-submitted.html")

def register_establishment(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        password_confirm = request.POST.get("password_confirm")

        business_name = request.POST.get("business_name")
        contact_number = request.POST.get("contact_number")
        address = request.POST.get("address")
        postal_code = request.POST.get("postal_code")
        general_location = request.POST.get("general_location")
        business_type = request.POST.get("business_type")
        description = request.POST.get("description")

        profile_image = request.FILES.get("profile_image")
        certification_file = request.FILES.get("certification_file")

        if password != password_confirm:
            return render(request, "foodrescue/public/register-establishment.html", {
                "error_message": "Passwords do not match."
            })

        if User.objects.filter(username=email).exists():
            return render(request, "foodrescue/public-pages/register-establishment.html", {
                "error_message": "An account with this email already exists."
            })

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        Establishment.objects.create(
            user=user,
            business_name=business_name,
            contact_number=contact_number,
            address=address,
            postal_code=postal_code,
            general_location=general_location,
            business_type=business_type,
            description=description,
            profile_image=profile_image,
            certification_file=certification_file,
            is_verified=False
        )

        return redirect("registration_submitted")

    return render(request, "foodrescue/public-pages/register-establishment.html")

@organisation_required
def organisation_profile(request):
    
    organisation = request.user.organisation_profile

    if request.method == "POST":
        organisation.organisation_name = request.POST.get("organisation_name", "")
        organisation.contact_number = request.POST.get("contact_number", "")
        organisation.address = request.POST.get("address", "")
        organisation.postal_code = request.POST.get("postal_code", "")
        organisation.team_size = request.POST.get("team_size") or None
        organisation.organisation_type = request.POST.get("organisation_type", "")
        organisation.general_location = request.POST.get("general_location", "")
        organisation.description = request.POST.get("description", "")

        if request.FILES.get("profile_image"):
            organisation.profile_image = request.FILES.get("profile_image")

        organisation.save()

        return redirect("organisation_profile")

    return render(request, "foodrescue/organisation-pages/organisation-profile.html", {
        "organisation": organisation,
    })
    
def logout_view(request):
    logout(request)
    return redirect("login")

def public_home(request):
    events = DistributionEvent.objects.select_related(
        "organisation"
    ).filter(
        status=DistributionEvent.Status.PUBLISHED
    ).order_by("event_date", "start_time")[:10]

    return render(request, "foodrescue/public-pages/public-home.html", {
        "events": events,
    })
    

@establishment_required
def establishment_dashboard(request):
    establishment = request.user.establishment_profile

    pending_reservations = Reservation.objects.select_related(
        "food_listing",
        "food_listing__establishment",
        "organisation"
    ).filter(
        food_listing__establishment=establishment,
        status=Reservation.Status.PENDING
    ).order_by("-created_at")

    accepted_pickups = Reservation.objects.select_related(
        "food_listing",
        "food_listing__establishment",
        "organisation"
    ).filter(
        food_listing__establishment=establishment,
        status=Reservation.Status.APPROVED
    ).order_by("pickup_date", "pickup_time")

    completed_pickups = Reservation.objects.filter(
        food_listing__establishment=establishment,
        status=Reservation.Status.COLLECTED
    ).count()

    food_listings_count = FoodListing.objects.filter(
        establishment=establishment
    ).count()

    total_food_donated = Reservation.objects.filter(
        food_listing__establishment=establishment,
        status=Reservation.Status.COLLECTED
    ).aggregate(
        total=Sum("food_listing__weight_kg")
    )["total"] or 0

    return render(request, "foodrescue/establishment-pages/establishment_dashboard.html", {
        "establishment": establishment,
        "reservations": pending_reservations,
        "accepted_pickups": accepted_pickups,
        "completed_pickups": completed_pickups,
        "food_listings_count": food_listings_count,
        "total_food_donated": total_food_donated,
    })
# Both organisation and establishment must mark the reservation as completed
# for the reservation to be completed
@organisation_required
@require_POST
def organisation_mark_pickup_completed(request, reservation_id):

    organisation = request.user.organisation_profile

    reservation = get_object_or_404(
        Reservation.objects.select_related("food_listing"),
        id=reservation_id,
        organisation=organisation,
        status=Reservation.Status.APPROVED
    )

    reservation.organisation_marked_completed = True

    if reservation.establishment_marked_completed:
        reservation.status = Reservation.Status.COLLECTED
        reservation.completed_at = timezone.now()

        reservation.food_listing.status = FoodListing.Status.COMPLETED
        reservation.food_listing.save()

    reservation.save()

    return redirect("organisation_dashboard")

@establishment_required
@require_POST
def establishment_mark_pickup_completed(request, reservation_id):

    establishment = request.user.establishment_profile

    reservation = get_object_or_404(
        Reservation.objects.select_related("food_listing", "food_listing__establishment"),
        id=reservation_id,
        food_listing__establishment=establishment,
        status=Reservation.Status.APPROVED
    )

    reservation.establishment_marked_completed = True

    if reservation.organisation_marked_completed:
        reservation.status = Reservation.Status.COLLECTED
        reservation.completed_at = timezone.now()

        reservation.food_listing.status = FoodListing.Status.COMPLETED
        reservation.food_listing.save()

    reservation.save()

    return redirect("establishment_dashboard")

@establishment_required
def establishment_profile(request):
    establishment = request.user.establishment_profile

    return render(request, "foodrescue/establishment-pages/establishment-profile.html", {
        "establishment": establishment,
    })
    
@establishment_required
def establishment_food_listing_detail(request, listing_id):

    establishment = request.user.establishment_profile

    food_listing = get_object_or_404(
        FoodListing.objects.select_related("establishment"),
        id=listing_id,
        establishment=establishment
    )

    reservations = Reservation.objects.select_related(
        "food_listing",
        "food_listing__establishment",
        "organisation"
    ).filter(
        food_listing=food_listing,
        status=Reservation.Status.PENDING
    ).order_by("-created_at")

    pickup_reservation = Reservation.objects.select_related(
        "organisation"
    ).filter(
        food_listing=food_listing,
        status__in=[
            Reservation.Status.APPROVED,
            Reservation.Status.COLLECTED
        ]
    ).first()

    return render(request, "foodrescue/establishment-pages/establishment-food-detail.html", {
        "food_listing": food_listing,
        "reservations": reservations,
        "pickup_reservation": pickup_reservation,
    })
    
@establishment_required
def establishment_food_listings(request):
    establishment = request.user.establishment_profile

    selected_category = request.GET.get("category", "")
    halal_only = request.GET.get("halal") == "true"
    sort_by = request.GET.get("sort", "newest")
    search_query = request.GET.get("q", "").strip()

    listings = FoodListing.objects.filter(
        establishment=establishment
    ).select_related(
        "establishment"
    ).annotate(
        pending_request_count=Count(
            "reservations",
            filter=Q(reservations__status=Reservation.Status.PENDING)
        )
    ).prefetch_related(
    Prefetch(
        "reservations",
        queryset=Reservation.objects.filter(
            status__in=[
                Reservation.Status.APPROVED,
                Reservation.Status.COLLECTED
            ]
        ).select_related("organisation"),
        to_attr="approved_reservations"
    )
)

    if selected_category:
        listings = listings.filter(category=selected_category)

    if halal_only:
        listings = listings.filter(is_halal=True)

    if search_query:
        listings = listings.filter(name__icontains=search_query)

    if sort_by == "oldest":
        listings = listings.order_by("created_at")
    else:
        listings = listings.order_by("-created_at")

    return render(request, "foodrescue/establishment-pages/establishment-food-listings.html", {
        "establishment": establishment,
        "listings": listings,
        "categories": FoodListing.Category.choices,
        "selected_category": selected_category,
        "halal_only": halal_only,
        "sort_by": sort_by,
        "search_query": search_query,
    })
    
def public_organisations(request):
    search_query = request.GET.get("q", "").strip()

    organisations = Organisation.objects.filter(
        is_verified=True
    ).order_by("organisation_name")

    if search_query:
        organisations = organisations.filter(
            Q(organisation_name__icontains=search_query) |
            Q(general_location__icontains=search_query)
        )

    for organisation in organisations:
        organisation.food_rescued_kg = Reservation.objects.filter(
            organisation=organisation,
            status=Reservation.Status.COLLECTED
        ).aggregate(
            total=Sum("food_listing__weight_kg")
        )["total"] or 0

        organisation.distribution_events_count = DistributionEvent.objects.filter(
            organisation=organisation,
            status=DistributionEvent.Status.PUBLISHED
        ).count()

    return render(request, "foodrescue/public-pages/public-organisations.html", {
        "organisations": organisations,
        "search_query": search_query,
    })
    
def public_organisation_profile(request, organisation_id):
    organisation = get_object_or_404(
        Organisation,
        id=organisation_id,
        is_verified=True
    )

    return render(request, "foodrescue/public-pages/public-organisation-profile.html", {
        "organisation": organisation
    })
    
def public_establishments(request):
    search_query = request.GET.get("q", "").strip()

    establishments = Establishment.objects.filter(
        is_verified=True
    ).order_by("business_name")

    if search_query:
        establishments = establishments.filter(
            Q(business_name__icontains=search_query) |
            Q(general_location__icontains=search_query) |
            Q(business_type__icontains=search_query)
        )

    for establishment in establishments:
        establishment.listings_count = FoodListing.objects.filter(
            establishment=establishment
        ).count()

        establishment.completed_donations_count = FoodListing.objects.filter(
            establishment=establishment,
            status=FoodListing.Status.COMPLETED
        ).count()

    return render(request, "foodrescue/public-pages/public-establishments.html", {
        "establishments": establishments,
        "search_query": search_query,
    })
    
def public_establishment_profile(request, establishment_id):
    establishment = get_object_or_404(
        Establishment,
        id=establishment_id,
        is_verified=True
    )

    return render(request, "foodrescue/public-pages/public-establishment-profile.html", {
        "establishment": establishment
    })
    
def public_distribution_events(request):
    selected_region = request.GET.get("region", "")

    events = DistributionEvent.objects.filter(
        status=DistributionEvent.Status.PUBLISHED
    ).order_by("event_date", "start_time")

    if selected_region:
        events = events.filter(area=selected_region)

    return render(request, "foodrescue/public-pages/public-distribution-events.html", {
        "events": events,
        "selected_region": selected_region,
        "regions": DistributionEvent.Area.choices,
    })
    
@establishment_required
def establishment_completed_pickups(request):
    establishment = request.user.establishment_profile

    completed_pickups = Reservation.objects.select_related(
        "food_listing",
        "food_listing__establishment",
        "organisation"
    ).filter(
        food_listing__establishment=establishment,
        status=Reservation.Status.COLLECTED
    ).order_by("-completed_at", "-pickup_date", "-pickup_time")

    return render(request, "foodrescue/establishment-pages/establishment_completed_pickups.html", {
        "establishment": establishment,
        "completed_pickups": completed_pickups,
    })