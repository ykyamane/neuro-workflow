#!/usr/bin/env python3
"""
Confirm a Supabase user's email so they can sign in with password.

Requires the project's SERVICE ROLE key (not the anon key).
Get it from: Supabase Dashboard → Project Settings → API → service_role (secret).

Usage:
  SUPABASE_URL="https://YOUR_PROJECT.supabase.co" \\
  SUPABASE_SERVICE_ROLE_KEY="your-service-role-key" \\
  python confirm_supabase_user_by_email.py user@example.com

Or export the env vars and run:
  python confirm_supabase_user_by_email.py user@example.com
"""
import os
import sys
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("Install requests: pip install requests", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) != 2:
        print("Usage: SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... python confirm_supabase_user_by_email.py <email>", file=sys.stderr)
        sys.exit(1)
    email = sys.argv[1].strip().lower()
    url = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY.", file=sys.stderr)
        sys.exit(1)
    auth_url = f"{url}/auth/v1"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    # List users and find by email
    r = requests.get(f"{auth_url}/admin/users", headers=headers, params={"per_page": 1000}, timeout=30)
    if r.status_code != 200:
        print(f"List users failed: {r.status_code} {r.text}", file=sys.stderr)
        sys.exit(1)
    data = r.json()
    users = data.get("users") or []
    user = next((u for u in users if (u.get("email") or "").lower() == email), None)
    if not user:
        print(f"No user found with email: {email}", file=sys.stderr)
        sys.exit(1)
    user_id = user.get("id")
    if not user_id:
        print("User object missing id.", file=sys.stderr)
        sys.exit(1)
    # Update user: set email_confirmed_at so they can sign in
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = {"email_confirm": True, "email_confirmed_at": now}
    r2 = requests.put(f"{auth_url}/admin/users/{user_id}", headers=headers, json=body, timeout=30)
    if r2.status_code not in (200, 204):
        print(f"Update user failed: {r2.status_code} {r2.text}", file=sys.stderr)
        sys.exit(1)
    print(f"Confirmed email for {email}. They can now log in with their password.")


if __name__ == "__main__":
    main()
