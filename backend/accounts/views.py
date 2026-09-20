import json
from hashlib import sha256
from functools import wraps

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .models import ClientUser
from assignments.models import AssignmentLot
from assignments.services import assignment_summary, create_default_lots

MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60


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
        "client_is_active": user.client_is_active,
    }


def _money(amount):
    return f"{amount:.2f}"


def _login_attempt_cache_key(request, username):
    remote_address = request.META.get("REMOTE_ADDR", "unknown")
    raw_key = f"{remote_address}:{username.casefold()}".encode("utf-8")
    return f"client-login-attempts:{sha256(raw_key).hexdigest()}"


def _lot_data(lot):
    return {
        "lot_number": lot.lot_number,
        "task_name": lot.task_name,
        "task_description": lot.task_description,
        "task_value": _money(lot.task_value),
        "employee_earning": _money(lot.employee_earning),
        "task_link": lot.task_link,
        "is_completed": lot.is_completed,
    }


def _assignment_data(summary):
    return {
        "total_lots": summary["total_lots"],
        "completed": summary["completed"],
        "remaining": summary["remaining"],
        "percentage": summary["percentage"],
        "current_earnings": _money(summary["current_earnings"]),
        "potential_earnings": _money(summary["potential_earnings"]),
        "remaining_potential": _money(summary["remaining_potential"]),
        "is_complete": summary["completed"] == summary["total_lots"],
        "lots": [_lot_data(lot) for lot in summary["lots"]],
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

    with transaction.atomic():
        user = ClientUser.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            referral_code=referral_code,
        )
        create_default_lots(user)
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

    attempt_key = _login_attempt_cache_key(request, username)
    if cache.get(attempt_key, 0) >= MAX_LOGIN_ATTEMPTS:
        return JsonResponse(
            {"detail": "Too many unsuccessful login attempts. Try again in 15 minutes."},
            status=429,
        )

    matching_email_user = ClientUser.objects.filter(email__iexact=username).first()
    username_to_authenticate = matching_email_user.username if matching_email_user else username
    user = authenticate(request, username=username_to_authenticate, password=password)
    if user is None:
        cache.add(attempt_key, 0, timeout=LOGIN_LOCKOUT_SECONDS)
        cache.incr(attempt_key)
        return JsonResponse({"detail": "Invalid username or password."}, status=401)

    cache.delete(attempt_key)
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
    return demo_dashboard(request)


@require_GET
@api_login_required
def demo_dashboard(request):
    summary = assignment_summary(request.user, AssignmentLot.AssignmentType.DEMO)
    return JsonResponse(
        {
            "user": _user_data(request.user),
            "account_type": "demo",
            "assignment": _assignment_data(summary),
            "client_access_available": request.user.client_is_active,
            "message": "Welcome to your demo assignment.",
        }
    )


@require_GET
@api_login_required
def client_dashboard(request):
    if not request.user.client_is_active:
        return JsonResponse({"detail": "Your client assignment has not been activated."}, status=403)

    summary = assignment_summary(request.user, AssignmentLot.AssignmentType.CLIENT)
    carried_demo_earnings = request.user.carried_demo_earnings
    client_earnings = summary["current_earnings"]
    return JsonResponse(
        {
            "user": _user_data(request.user),
            "account_type": "client",
            "assignment": _assignment_data(summary),
            "demo_earnings_carried_forward": _money(carried_demo_earnings),
            "client_earnings": _money(client_earnings),
            "total_earnings": _money(carried_demo_earnings + client_earnings),
            "message": "Welcome to your client assignment.",
        }
    )

# Create your views here.
