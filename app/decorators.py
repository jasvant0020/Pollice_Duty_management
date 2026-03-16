from django.shortcuts import redirect
from django.contrib import messages

def role_required(allowed_roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("login")

            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            messages.error(request, "You do not have permission to access this page.")
            return redirect("login")
        return wrapper
    return decorator
