"""
RAVEN Policy Management REST Router Module

Provides REST endpoints for merchant policy configuration lifecycle:
drafting, validation, simulation, activation, rollback, version history, and audit lineage.
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from apps.api.auth import UserIdentity, get_current_user, require_permission
from apps.api.dependencies import get_policy_service
from apps.api.policy_service import PolicyService, PolicySimulationResponse
from domain.entities.merchant_policy import MerchantPolicyVersion, PolicyAuditLog

router = APIRouter(prefix="/api/v1/operations/policies", tags=["Merchant Policies"])


class CreatePolicyDraftRequest(BaseModel):
    """Request payload for creating a new DRAFT policy version."""

    policy_id: str = Field("pol_default", description="Policy identifier")
    configuration_json: dict[str, Any] = Field(..., description="Rule parameter overrides dictionary")


class ValidatePolicyRequest(BaseModel):
    """Request payload for validating policy parameters."""

    configuration_json: dict[str, Any] = Field(..., description="Rule parameter overrides dictionary")


class SimulatePolicyRequest(BaseModel):
    """Request payload for dry-run policy simulation."""

    configuration_json: dict[str, Any] = Field(..., description="Candidate rule parameter overrides dictionary")


class ActivatePolicyRequest(BaseModel):
    """Request payload for activating a policy version."""

    version: int = Field(..., ge=1, description="Policy version number to activate")
    reason: str = Field("Manual policy activation", description="Reason for activation")


class RollbackPolicyRequest(BaseModel):
    """Request payload for rolling back to a historical policy version."""

    target_version: int = Field(..., ge=1, description="Historical version number to roll back to")
    reason: str = Field("Manual policy rollback", description="Reason for rollback")


@router.get("", response_model=list[MerchantPolicyVersion])
def list_policies(
    service: PolicyService = Depends(get_policy_service),
    user: UserIdentity = Depends(get_current_user),
) -> list[MerchantPolicyVersion]:
    """Lists all policy versions for the authenticated tenant."""
    return service.list_versions(user.tenant_id)


@router.get("/{policy_id}", response_model=MerchantPolicyVersion)
def get_active_policy(
    policy_id: str,
    service: PolicyService = Depends(get_policy_service),
    user: UserIdentity = Depends(get_current_user),
) -> MerchantPolicyVersion:
    """Retrieves the currently ACTIVE policy version for the authenticated tenant."""
    active = service.get_active(user.tenant_id)
    if not active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "NOT_FOUND", "message": f"No ACTIVE policy found for tenant '{user.tenant_id}'."}},
        )
    return active


@router.get("/{policy_id}/versions", response_model=list[MerchantPolicyVersion])
def list_policy_versions(
    policy_id: str,
    service: PolicyService = Depends(get_policy_service),
    user: UserIdentity = Depends(get_current_user),
) -> list[MerchantPolicyVersion]:
    """Lists all historical and current policy versions for a specific policy ID."""
    return service.list_versions(user.tenant_id)


@router.post("", response_model=MerchantPolicyVersion, status_code=status.HTTP_201_CREATED)
def create_draft_policy(
    request_body: CreatePolicyDraftRequest,
    request: Request,
    service: PolicyService = Depends(get_policy_service),
    user: UserIdentity = Depends(require_permission("POLICY_WRITE")),
) -> MerchantPolicyVersion:
    """Creates a new DRAFT policy version for the authenticated tenant."""
    req_id = getattr(request.state, "request_id", "req_unknown")
    try:
        version, _ = service.create_draft(
            tenant_id=user.tenant_id,
            policy_id=request_body.policy_id,
            configuration_json=request_body.configuration_json,
            actor_id=user.key_id,
            request_id=req_id,
        )
        return version
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "VALIDATION_ERROR", "message": str(exc)}},
        )


@router.post("/{policy_id}/validate", response_model=dict[str, Any])
def validate_policy(
    policy_id: str,
    request_body: ValidatePolicyRequest,
    service: PolicyService = Depends(get_policy_service),
    user: UserIdentity = Depends(get_current_user),
) -> dict[str, Any]:
    """Validates candidate policy parameters without mutating state."""
    is_valid, errors = service.validate(request_body.configuration_json)
    return {
        "policy_id": policy_id,
        "is_valid": is_valid,
        "errors": errors,
    }


@router.post("/{policy_id}/simulate", response_model=PolicySimulationResponse)
def simulate_policy(
    policy_id: str,
    request_body: SimulatePolicyRequest,
    service: PolicyService = Depends(get_policy_service),
    user: UserIdentity = Depends(get_current_user),
) -> PolicySimulationResponse:
    """
    Executes a dry-run policy simulation comparing candidate configuration against benchmark cases.
    GUARANTEED ZERO SIDE EFFECTS, ZERO TOKEN ISSUANCE, ZERO DB MUTATIONS.
    """
    return service.simulate(user.tenant_id, request_body.configuration_json)


@router.post("/{policy_id}/activate", response_model=MerchantPolicyVersion)
def activate_policy(
    policy_id: str,
    request_body: ActivatePolicyRequest,
    request: Request,
    service: PolicyService = Depends(get_policy_service),
    user: UserIdentity = Depends(require_permission("POLICY_ACTIVATE")),
) -> MerchantPolicyVersion:
    """
    Transactionally activates a policy version.
    Requires POLICY_ACTIVATE permission.
    """
    req_id = getattr(request.state, "request_id", "req_unknown")
    try:
        return service.activate(
            tenant_id=user.tenant_id,
            version=request_body.version,
            actor_id=user.key_id,
            reason=request_body.reason,
            request_id=req_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "ACTIVATION_FAILED", "message": str(exc)}},
        )


@router.post("/{policy_id}/rollback", response_model=MerchantPolicyVersion)
def rollback_policy(
    policy_id: str,
    request_body: RollbackPolicyRequest,
    request: Request,
    service: PolicyService = Depends(get_policy_service),
    user: UserIdentity = Depends(require_permission("POLICY_ROLLBACK")),
) -> MerchantPolicyVersion:
    """
    Performs lineage-preserving rollback to a target historical policy version.
    Creates a NEW version copying target configuration and sets it ACTIVE.
    Requires POLICY_ROLLBACK permission.
    """
    req_id = getattr(request.state, "request_id", "req_unknown")
    try:
        return service.rollback(
            tenant_id=user.tenant_id,
            target_version=request_body.target_version,
            actor_id=user.key_id,
            reason=request_body.reason,
            request_id=req_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "ROLLBACK_FAILED", "message": str(exc)}},
        )


@router.get("/{policy_id}/audit", response_model=list[PolicyAuditLog])
def list_policy_audit_logs(
    policy_id: str,
    service: PolicyService = Depends(get_policy_service),
    user: UserIdentity = Depends(get_current_user),
) -> list[PolicyAuditLog]:
    """Lists audit logs for the authenticated tenant's policy mutations."""
    return service.list_audit_logs(user.tenant_id)
