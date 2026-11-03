from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import FarmInvitation, FarmMembership, FarmMembershipAudit
from .tasks import send_farm_invitation_email


def actor_membership(farm, actor):
    membership = FarmMembership.objects.filter(farm=farm, user=actor, is_active=True).first()
    if membership is None or membership.role not in {
        FarmMembership.Role.OWNER,
        FarmMembership.Role.MANAGER,
    }:
        raise PermissionDenied("Only owners and managers can manage the farm team")
    return membership


def require_can_manage_role(actor_role, target_role):
    if actor_role != FarmMembership.Role.OWNER and target_role in {
        FarmMembership.Role.OWNER,
        FarmMembership.Role.MANAGER,
    }:
        raise PermissionDenied("Only owners can manage owner or manager roles")


@transaction.atomic
def invite_member(*, farm, actor, email, role):
    actor_record = actor_membership(farm, actor)
    require_can_manage_role(actor_record.role, role)
    email = email.strip().lower()
    if FarmMembership.objects.filter(farm=farm, user__email__iexact=email, is_active=True).exists():
        raise ValidationError({"email": "This user is already an active farm member"})
    FarmInvitation.objects.filter(
        farm=farm, email__iexact=email, status=FarmInvitation.Status.PENDING
    ).update(status=FarmInvitation.Status.REVOKED)
    invitation = FarmInvitation.objects.create(
        farm=farm,
        email=email,
        role=role,
        expires_at=timezone.now() + timedelta(days=7),
        invited_by=actor,
    )
    FarmMembershipAudit.objects.create(
        farm=farm,
        event_type=FarmMembershipAudit.EventType.INVITED,
        subject_email=email,
        to_role=role,
        actor=actor,
    )
    transaction.on_commit(
        lambda invitation_id=str(invitation.id): send_farm_invitation_email.delay(invitation_id)
    )
    return invitation


@transaction.atomic
def accept_invitation(*, token, user):
    invitation = FarmInvitation.objects.select_for_update().filter(token=token).first()
    if invitation is None or invitation.status != FarmInvitation.Status.PENDING:
        raise ValidationError({"token": "Invitation is invalid or no longer pending"})
    if invitation.is_expired:
        raise ValidationError({"token": "Invitation has expired"})
    if not user.email or user.email.lower() != invitation.email.lower():
        raise PermissionDenied("Sign in with the email address that was invited")
    membership, _ = FarmMembership.objects.update_or_create(
        farm=invitation.farm,
        user=user,
        defaults={"role": invitation.role, "is_active": True},
    )
    invitation.status = FarmInvitation.Status.ACCEPTED
    invitation.accepted_by = user
    invitation.save(update_fields=["status", "accepted_by", "updated_at"])
    FarmMembershipAudit.objects.create(
        farm=invitation.farm,
        event_type=FarmMembershipAudit.EventType.ACCEPTED,
        subject_email=user.email,
        to_role=invitation.role,
        actor=user,
    )
    return membership


@transaction.atomic
def update_membership(*, membership, actor, role=None, is_active=None):
    actor_record = actor_membership(membership.farm, actor)
    require_can_manage_role(actor_record.role, membership.role)
    if role is not None:
        require_can_manage_role(actor_record.role, role)
    if membership.user_id == actor.id and is_active is False:
        raise ValidationError({"is_active": "You cannot deactivate your own membership"})
    removing_owner = membership.role == FarmMembership.Role.OWNER and (
        is_active is False or (role is not None and role != FarmMembership.Role.OWNER)
    )
    if removing_owner:
        other_owners = FarmMembership.objects.filter(
            farm=membership.farm,
            role=FarmMembership.Role.OWNER,
            is_active=True,
        ).exclude(pk=membership.pk)
        if not other_owners.exists():
            raise ValidationError("A farm must retain at least one active owner")
    old_role = membership.role
    old_active = membership.is_active
    if role is not None:
        membership.role = role
    if is_active is not None:
        membership.is_active = is_active
    membership.save(update_fields=["role", "is_active", "updated_at"])
    if old_role != membership.role:
        event = FarmMembershipAudit.EventType.ROLE_CHANGED
    elif old_active and not membership.is_active:
        event = FarmMembershipAudit.EventType.DEACTIVATED
    else:
        event = FarmMembershipAudit.EventType.REACTIVATED
    FarmMembershipAudit.objects.create(
        farm=membership.farm,
        event_type=event,
        subject_email=membership.user.email,
        from_role=old_role,
        to_role=membership.role,
        actor=actor,
    )
    return membership


@transaction.atomic
def revoke_invitation(*, invitation, actor):
    actor_record = actor_membership(invitation.farm, actor)
    require_can_manage_role(actor_record.role, invitation.role)
    if invitation.status != FarmInvitation.Status.PENDING:
        raise ValidationError("Only pending invitations can be revoked")
    invitation.status = FarmInvitation.Status.REVOKED
    invitation.save(update_fields=["status", "updated_at"])
    FarmMembershipAudit.objects.create(
        farm=invitation.farm,
        event_type=FarmMembershipAudit.EventType.INVITATION_REVOKED,
        subject_email=invitation.email,
        from_role=invitation.role,
        actor=actor,
    )
    return invitation
