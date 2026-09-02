"""
Razorpay Webhook Ingestion Router Module

Exposes POST /api/v1/webhooks/razorpay endpoint for receiving and verifying raw Razorpay webhooks.
"""

from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.responses import JSONResponse
from apps.api.dependencies import get_webhook_service
from apps.api.schemas import ErrorResponse, WebhookResponse
from apps.api.webhook_service import WebhookProcessingError, WebhookService

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])


@router.post(
    "/razorpay",
    response_model=WebhookResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Malformed JSON or mapping failure"},
        401: {"model": ErrorResponse, "description": "Missing or invalid HMAC-SHA256 signature"},
    },
)
async def ingest_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None, alias="X-Razorpay-Signature"),
    x_razorpay_event_id: str | None = Header(default=None, alias="X-Razorpay-Event-Id"),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> WebhookResponse | JSONResponse:
    """
    Ingests raw Razorpay webhook payload, verifies HMAC signature, maps canonical event,
    and executes autonomous recovery pipeline.
    """
    raw_body = await request.body()
    sig = x_razorpay_signature or request.headers.get("x-razorpay-signature")
    event_id = x_razorpay_event_id or request.headers.get("x-razorpay-event-id")

    try:
        response = webhook_service.process_razorpay_webhook(raw_body=raw_body, signature=sig, event_id_header=event_id)
        return response

    except WebhookProcessingError as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "status": "error",
                "error_code": e.error_code,
                "message": e.message,
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "error_code": "INTERNAL_SERVER_ERROR",
                "message": f"Unexpected webhook ingestion failure: {str(e)}",
            },
        )
