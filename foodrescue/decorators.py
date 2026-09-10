from functools import wraps
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def organisation_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):

        if not hasattr(request.user, "organisation_profile"):
            return render(
                request,
                "foodrescue/access-denied.html",
                status=403
            )

        organisation = request.user.organisation_profile

        if not organisation.is_verified:
            return render(
                request,
                "foodrescue/access-denied.html",
                {
                    "message": "Your organisation account has not been verified yet."
                },
                status=403
            )

        return view_func(request, *args, **kwargs)

    return wrapper


def establishment_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):

        if not hasattr(request.user, "establishment_profile"):
            return render(
                request,
                "foodrescue/access-denied.html",
                status=403
            )

        establishment = request.user.establishment_profile

        if not establishment.is_verified:
            return render(
                request,
                "foodrescue/access-denied.html",
                {
                    "message": "Your establishment account has not been verified yet."
                },
                status=403
            )

        return view_func(request, *args, **kwargs)

    return wrapper