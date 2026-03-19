from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from app.models import User
from .serializers import LoginSerializer, UserSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import logging



logger = logging.getLogger("api")



@api_view(["POST"])
def login_api(request):
    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]

    try:
        user_obj = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {"success": False, "message": "Email not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    user = authenticate(username=user_obj.username, password=password)

    if user is None:
        return Response(
            {"success": False, "message": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    refresh = RefreshToken.for_user(user)

    logger.info(
        f"LOGIN API | User={user.email} | Role={user.role} | IP={request.META.get('REMOTE_ADDR')}"
    )


    return Response({
        "success": True,
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": UserSerializer(user).data
    })

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_api(request):
    try:
        refresh_token = request.data.get("refresh")
        token = RefreshToken(refresh_token)
        token.blacklist()

        logger.info(
            f"LOGOUT API | User={request.user.email} | Role={request.user.role}"
        )

        return Response(
            {"success": True, "message": "Logged out successfully"},
            status=status.HTTP_200_OK
        )

    except Exception:
        return Response(
            {"success": False, "message": "Invalid token"},
            status=status.HTTP_400_BAD_REQUEST
        )


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from app.models import VVIPDuty, DutyAttendance
from app.utils.geo import calculate_distance  # or paste function here

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def update_staff_location(request):
    user = request.user

    lat = float(request.data.get("lat"))
    lng = float(request.data.get("lng"))

    active_duties = VVIPDuty.objects.filter(
        field_staff=user,
        is_active=True,
        geo_enabled=True
    )

    for duty in active_duties:

        distance = calculate_distance(
            lat, lng,
            duty.latitude,
            duty.longitude
        )

        attendance, _ = DutyAttendance.objects.get_or_create(
            staff=user,
            duty=duty
        )

        # ✅ ENTER
        if distance <= duty.radius:
            if not attendance.is_inside:
                attendance.is_inside = True
                attendance.check_in_time = timezone.now()

        # ❌ EXIT
        else:
            if attendance.is_inside:
                attendance.is_inside = False
                attendance.check_out_time = timezone.now()

        attendance.save()

    return Response({"status": "updated"})