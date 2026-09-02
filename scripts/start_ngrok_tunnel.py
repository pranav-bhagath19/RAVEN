"""
RAVEN Ngrok Public Tunnel Forwarder (Python SDK)

Exposes local FastAPI backend on port 8000 to the internet for Razorpay Webhook testing.
Uses official `ngrok` Python SDK installed via `pip install ngrok`.

Usage:
    python scripts/start_ngrok_tunnel.py
"""

import os
import sys
import time

try:
    import ngrok
except ImportError:
    print("[ERROR] 'ngrok' Python package is not installed. Run: pip install ngrok")
    sys.exit(1)


def start_tunnel(port: int = 8000) -> None:
    authtoken = os.getenv("NGROK_AUTHTOKEN", "3ApsZO8ocSWdUy3yyAoaw89LaU5_tVT8SsGAXFFpCtLmiWA")
    domain = os.getenv("NGROK_DOMAIN", "").strip() or None

    print("=" * 72)
    print("  RAVEN — NGROK WEBHOOK TUNNEL FORWARDER")
    print("=" * 72)
    print()
    print(f"  Configured Authtoken: {authtoken[:10]}***")
    if domain:
        print(f"  Configured Static Domain: {domain}")
    print()

    try:
        print(f"  [STEP 1/2] Connecting ngrok tunnel to localhost:{port}...")
        kwargs = {"authtoken": authtoken}
        if domain:
            kwargs["domain"] = domain

        listener = ngrok.forward(port, **kwargs)  # type: ignore[arg-type]
        public_url = listener.url()
        webhook_url = f"{public_url}/api/v1/webhooks/razorpay"

        print("  [STEP 2/2] Public Tunnel Established!")
        print(f"  -> Base Public URL:  {public_url}")
        print(f"  -> Razorpay Webhook: {webhook_url}")
        print()
        print("=" * 72)
        print("  RAZORPAY DASHBOARD WEBHOOK CONFIGURATION:")
        print("  1. Go to https://dashboard.razorpay.com/ (Test Mode)")
        print("  2. Settings -> Webhooks -> Add New Webhook")
        print(f"  3. Webhook URL: {webhook_url}")
        print("  4. Secret:      (Match RAZORPAY_WEBHOOK_SECRET in .env)")
        print("  5. Event:       payment.failed")
        print("=" * 72)
        print()
        print("Press Ctrl+C to stop the tunnel...")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping ngrok tunnel...")
        sys.exit(0)
    except Exception as e:
        err_msg = str(e)
        print(f"\n[FAIL] Failed to establish ngrok tunnel: {err_msg}")
        if "ERR_NGROK_15013" in err_msg or "dev domain" in err_msg:
            print()
            print("=" * 72)
            print("  NGROK DOMAIN ACTION REQUIRED:")
            print("  1. Go to https://dashboard.ngrok.com/domains")
            print("  2. Copy your free static domain (e.g. 'xxxx-xx-xx.ngrok-free.app')")
            print("  3. Add it to .env:  NGROK_DOMAIN=xxxx-xx-xx.ngrok-free.app")
            print("  4. Re-run: python scripts/start_ngrok_tunnel.py")
            print("=" * 72)
        sys.exit(1)


if __name__ == "__main__":
    start_tunnel(8000)
