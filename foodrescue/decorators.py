from functools import wraps
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def organisation_required(view_func):
    """
    Decorator used to protect organisation-only views.

    The user must be logged in, must have an organisation profile,
    and must have alrady been verified by an admin.

    If any check fails, the user is shown an access denied page.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Check that the logged-in user is registered as an organisation.
        if not hasattr(request.user, "organisation_profile"):
            return render(
                request,
                "foodrescue/access-denied.html",
                status=403
            )

        organisation = request.user.organisation_profile
        # Prevent unverified organisations from accessing protected features.
        if not organisation.is_verified:
            return render(
                request,
                "foodrescue/access-denied.html",
                {
                    "message": "Your organisation account has not been verified yet."
                },
                status=403
            )
        # Run the original view only after all access checks pass.
        return view_func(request, *args, **kwargs)

    return wrapper


def establishment_required(view_func):
    """
    Decorator used to protect establishment-only views.
    
    The user must be logged in, must have an establishment profile,
    and must have alrady been verified by an admin.
        
    If any check fails, the user is shown an access denied page.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
         # Check that the logged-in user is registered as an establishment.
        if not hasattr(request.user, "establishment_profile"):
            return render(
                request,
                "foodrescue/access-denied.html",
                status=403
            )

        establishment = request.user.establishment_profile
        # Prevent unverified establishments from accessing protected features.
        if not establishment.is_verified:
            return render(
                request,
                "foodrescue/access-denied.html",
                {
                    "message": "Your establishment account has not been verified yet."
                },
                status=403
            )
        # Run the original view only after all access checks pass.
        return view_func(request, *args, **kwargs)

    return wrapper