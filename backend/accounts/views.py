import json
from functools import wraps

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .models import ClientUser


def _json_body(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, JsonResponse({"detail": "Request body must be valid JSON."}, status=400)

    if not isinstance(payload, dict):
        return None, JsonResponse({"detail": "Request body must be a JSON object."}, status=400)
    return payload, None


def _user_data(user):
    return {
        "id": user.pk,
        "full_name": user.full_name,
        "email": user.email,
        "username": user.username,
        "referral_code": user.referral_code,
    }


def api_login_required(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication is required."}, status=401)
        return view(request, *args, **kwargs)

    return wrapped


@require_GET
@ensure_csrf_cookie
def csrf(request):
    """Sets the CSRF cookie needed before browser-based JSON POST requests."""
    return JsonResponse({"detail": "CSRF cookie set."})


@require_POST
def signup(request):
    payload, error = _json_body(request)
    if error:
        return error

    full_name = str(payload.get("full_name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    referral_code = str(payload.get("referral_code", "")).strip()
    password = str(payload.get("password", ""))

    missing = [
        field
        for field, value in {
            "full_name": full_name,
            "email": email,
            "referral_code": referral_code,
            "password": password,
        }.items()
        if not value
    ]
    if missing:
        return JsonResponse({"detail": "All signup fields are required.", "errors": missing}, status=400)

    if ClientUser.objects.filter(email__iexact=email).exists():
        return JsonResponse({"detail": "An account with this email already exists."}, status=409)

    first_name, *remaining_name = full_name.split(maxsplit=1)
    last_name = remaining_name[0] if remaining_name else ""
    candidate = ClientUser(
        username=email,
        email=email,
        first_name=first_name,
        last_name=last_name,
        referral_code=referral_code,
    )
    try:
        validate_password(password, candidate)
    except ValidationError as validation_error:
        return JsonResponse({"detail": "Password does not meet requirements.", "errors": validation_error.messages}, status=400)

    user = ClientUser.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        referral_code=referral_code,
    )
    login(request, user)
    return JsonResponse({"user": _user_data(user)}, status=201)


@require_POST
def client_login(request):
    payload, error = _json_body(request)
    if error:
        return error

    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    if not username or not password:
        return JsonResponse({"detail": "Username and password are required."}, status=400)

    matching_email_user = ClientUser.objects.filter(email__iexact=username).first()
    username_to_authenticate = matching_email_user.username if matching_email_user else username
    user = authenticate(request, username=username_to_authenticate, password=password)
    if user is None:
        return JsonResponse({"detail": "Invalid username or password."}, status=401)

    login(request, user)
    return JsonResponse({"user": _user_data(user)})


@require_POST
@api_login_required
def client_logout(request):
    logout(request)
    return JsonResponse({"detail": "Signed out."})


@require_GET
@api_login_required
def profile(request):
    return JsonResponse({"user": _user_data(request.user)})


@require_GET
@api_login_required
def dashboard(request):
    return JsonResponse(
        {
            "user": _user_data(request.user),
            "message": "Welcome to the Hines client dashboard.",
        }
    )

# Create your views here.
