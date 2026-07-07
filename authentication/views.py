from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from google.auth.transport import requests
from google.oauth2 import id_token
from .models import Profile
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# Your Google Client ID from Google Cloud Console
GOOGLE_CLIENT_ID = "939210716621-jtf38t8tluotrd0jb467uo6f9vm9nnqn.apps.googleusercontent.com"  # Replace with your actual Client ID


class FlexibleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        identifier = request.data.get('username')
        password = request.data.get('password')

        identifier_m = identifier.replace(" ", "_") if identifier else None  # Remove spaces from identifier
        print(f"Login attempt with identifier: {identifier_m}")
        if not identifier_m or not password:
            return Response(
                {'error': 'username and password are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=identifier_m, password=password)

        if user is None:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile, _ = Profile.objects.get_or_create(user=user)
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'profile_complete': profile.profile_complete,
                'user_id': user.id,
                'user': {
                    'id': user.id,
                    'username': user.username.replace("_", " "),  # Replace underscores with spaces for display
                    'email': user.email,
                    'status': profile.status,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                },
            },
            status=status.HTTP_200_OK,
        )


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        password_confirm = request.data.get('password_confirm')
        status_choice = request.data.get('status', 'student')

        username_m = username.replace(" ", "_") if username else None  # Remove spaces from username
        print(f"Registration attempt with username: {username_m}, email: {email}, status: {status_choice}")
        # Validation
        if not username_m or not email or not password or not password_confirm:
            return Response(
                {'error': 'username, email, password, and password_confirm are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if password != password_confirm:
            return Response(
                {'error': 'Passwords do not match'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if user already exists
        if User.objects.filter(username=username_m).exists():
            return Response(
                {'error': 'Username already exists'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {'error': 'Email already exists'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate password strength
        try:
            validate_password(password)
        except ValidationError as e:
            return Response(
                {'error': list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Create user
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                )

                # The Profile post_save signal may already create this row.
                profile, _ = Profile.objects.get_or_create(user=user)
                profile.status = status_choice
                profile.profile_complete = True
                profile.save()

            logger.info(f"New user registered: {email} with status {status_choice}")

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'profile_complete': True,
                    'user_id': user.id,
                    'user': {
                        'id': user.id,
                        'username': user.username.replace("_", " "),  # Replace underscores with spaces for display
                        'email': user.email,
                    },
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Registration error: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to create user', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



@api_view(['POST'])
def google_login(request):
    """
    Handles Google Sign-In authentication using id_token.
    Frontend sends id_token from Google Sign-In, backend validates it and creates/authenticates user.
    Returns JWT tokens and `profile_complete` flag.
    """
    try:
        id_token_str = request.data.get('id_token')
        
        if not id_token_str:
            return Response(
                {'error': 'id_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify the token with Google
        try:
            idinfo = id_token.verify_oauth2_token(
                id_token_str,
                requests.Request(),
                GOOGLE_CLIENT_ID
            )
        except ValueError as e:
            logger.error(f"Invalid id_token: {str(e)}")
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Extract user info from token
        email = idinfo.get('email')
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')
        google_id = idinfo.get('sub')
        
        if not email:
            return Response(
                {'error': 'Email not provided in token'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get or create user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'username': f'user_{google_id[:10]}', 'first_name': '', 'last_name': ''}
        )
        
        profile, _ = Profile.objects.get_or_create(user=user)

        # If user was just created, keep profile incomplete
        if created:
            profile.profile_complete = False
            profile.save()
            logger.info(f"New user created: {email}")
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'profile_complete': profile.profile_complete,
            'user_id': user.id,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Google login error: {str(e)}")
        return Response(
            {'error': 'Authentication failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_profile(request):
    """Complete user profile (username, status) after social sign-in."""
    try:
        user = request.user
        username = request.data.get('username')
        status_choice = request.data.get('status')

        username_m = username.replace(" ", "_") if username else None  # Remove spaces from username

        print(f"Complete profile request - User: {user.email}, Username: {username_m}, Status: {status_choice}")

        logger.info(f"Complete profile request - User: {user.email}, Username: {username_m}, Status: {status_choice}")

        if not username_m:
            logger.warning(f"Missing username from {user.email}")
            return Response({'error': 'username is required'}, status=status.HTTP_400_BAD_REQUEST)

        user.username = username_m
        user.save()
        logger.info(f"Updated username for {user.email} to {username_m}")

        profile = user.profile
        if status_choice:
            profile.status = status_choice
        profile.profile_complete = True
        profile.save()
        logger.info(f"Marked profile complete for {user.email}")

        return Response({'message': 'Profile updated successfully!', 'username': username_m.replace("_", " "), 'status': status_choice}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Complete profile error: {str(e)}", exc_info=True)
        return Response({'error': 'Failed to update profile', 'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
