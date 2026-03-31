from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.text import slugify
from .models import Organization, Membership
from .serializers import OrganizationSerializer, MembershipSerializer
from .permissions import IsTenantAdmin, IsTenantOwner


class OrganizationCreateView(generics.CreateAPIView):
    """Create a new organization. Creator becomes OWNER automatically."""
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        org = serializer.save(slug=slugify(serializer.validated_data['name']))
        Membership.objects.create(
            user=self.request.user,
            organization=org,
            role=Membership.Role.OWNER
        )


class OrganizationDetailView(generics.RetrieveUpdateAPIView):
    """Retrieve or update organization details. Admins only."""
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def get_object(self):
        return self.request.organization


class MemberListView(generics.ListAPIView):
    """List all members of the current organization."""
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def get_queryset(self):
        return Membership.objects.filter(
            organization=self.request.organization
        ).select_related('user', 'organization')


class MemberInviteView(generics.CreateAPIView):
    """Invite an existing user to the organization."""
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def create(self, request, *args, **kwargs):
        from accounts.models import User
        email = request.data.get('email')
        role = request.data.get('role', Membership.Role.MEMBER)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'No user with this email exists.'},
                status=status.HTTP_404_NOT_FOUND
            )

        membership, created = Membership.objects.get_or_create(
            user=user,
            organization=request.organization,
            defaults={'role': role}
        )

        if not created:
            return Response(
                {'error': 'User is already a member.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(MembershipSerializer(membership).data, status=status.HTTP_201_CREATED)

# Create your views here.
