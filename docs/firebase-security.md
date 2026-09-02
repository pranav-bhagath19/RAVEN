# RAVEN Firebase Security & Isolation Specifications

## Tenant Isolation Boundary
All Firestore document collections require `tenant_id` scoping.
Cross-tenant reads/writes fail closed.

## Rules Specification (`firestore.rules`)
Production Security Rules enforce strict document-level authorization and tenant ownership verification.
