from django import forms
from .models import FoodListing, Reservation


class FoodListingForm(forms.ModelForm):
    """
    Form used by establishments to create surplus food listings.

    """
    class Meta:
        model = FoodListing
        fields = [
            "name",
            "category",
            "description",
            "allergens",
            "weight_kg",
            "quantity",
            "expiry_date",
            "is_halal",
            "pickup_location",
            "image",
        ]

        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "expiry_date": forms.DateInput(attrs={"type": "date"}),
        }


class ReservationForm(forms.ModelForm):
    """
    Form used by organisations to submit pickup reservation requests.

    """
    class Meta:
        model = Reservation
        fields = [
            "message",
            "pickup_date",
            "pickup_time",
        ]

        widgets = {
            "pickup_date": forms.DateInput(attrs={"type": "date"}),
            "pickup_time": forms.TimeInput(attrs={"type": "time"}),
            "message": forms.Textarea(attrs={"rows": 4}),
            "placeholder": "Add any special remarks here...",
        }