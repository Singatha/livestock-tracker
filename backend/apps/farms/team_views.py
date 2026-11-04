from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.throttling import PostScopedRateThrottle

from .models import FarmInvitation, FarmMembership, FarmMembershipAudit
from .permissions import selected_farm
from .team_serializers import (
    AcceptInvitationSerializer,
    FarmInvitationSerializer,
    FarmMembershipAuditSerializer,
    FarmMembershipSerializer,
    InviteMemberSerializer,
    UpdateMembershipSerializer,
)
from .team_services import (
    accept_invitation,
    actor_membership,
    invite_member,
    revoke_invitation,
    update_membership,
)


class TeamMembersView(APIView):
    @extend_schema(responses=FarmMembershipSerializer(many=True))
    def get(self, request):
        farm = selected_farm(request)
        actor_membership(farm, request.user)
        members = FarmMembership.objects.filter(farm=farm).select_related("user")
        return Response(FarmMembershipSerializer(members, many=True).data)


class TeamMemberDetailView(APIView):
    @extend_schema(request=UpdateMembershipSerializer, responses=FarmMembershipSerializer)
    def patch(self, request, membership_id):
        farm = selected_farm(request)
        membership = FarmMembership.objects.filter(farm=farm, id=membership_id).first()
        if membership is None:
            return Response({"detail": "Membership not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = UpdateMembershipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = update_membership(
            membership=membership, actor=request.user, **serializer.validated_data
        )
        return Response(FarmMembershipSerializer(membership).data)


class TeamInvitationsView(APIView):
    throttle_classes = [PostScopedRateThrottle]
    throttle_scope = "farm_invitations"

    @extend_schema(responses=FarmInvitationSerializer(many=True))
    def get(self, request):
        farm = selected_farm(request)
        actor_membership(farm, request.user)
        invitations = FarmInvitation.objects.filter(farm=farm)
        return Response(FarmInvitationSerializer(invitations, many=True).data)

    @extend_schema(request=InviteMemberSerializer, responses=FarmInvitationSerializer)
    def post(self, request):
        farm = selected_farm(request)
        serializer = InviteMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = invite_member(farm=farm, actor=request.user, **serializer.validated_data)
        return Response(FarmInvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)


class AcceptInvitationView(APIView):
    @extend_schema(request=AcceptInvitationSerializer, responses=FarmMembershipSerializer)
    def post(self, request):
        serializer = AcceptInvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = accept_invitation(user=request.user, **serializer.validated_data)
        return Response(FarmMembershipSerializer(membership).data)


class TeamInvitationDetailView(APIView):
    @extend_schema(responses={204: None})
    def delete(self, request, invitation_id):
        farm = selected_farm(request)
        invitation = FarmInvitation.objects.filter(farm=farm, id=invitation_id).first()
        if invitation is None:
            return Response({"detail": "Invitation not found"}, status=status.HTTP_404_NOT_FOUND)
        revoke_invitation(invitation=invitation, actor=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class TeamAuditView(APIView):
    @extend_schema(responses=FarmMembershipAuditSerializer(many=True))
    def get(self, request):
        farm = selected_farm(request)
        actor_membership(farm, request.user)
        audits = FarmMembershipAudit.objects.filter(farm=farm).select_related("actor")[:100]
        return Response(FarmMembershipAuditSerializer(audits, many=True).data)
