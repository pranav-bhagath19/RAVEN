"""
RAVEN AuditEvent Domain Entity Alias
"""

from domain.entities.audit import AuditEvent
from domain.enums import ActorType

__all__ = ["AuditEvent", "ActorType"]
