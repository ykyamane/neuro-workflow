# Log in after sign-up (Supabase)

The Workflow UI and BrainScaler use **Supabase** for auth. Login can fail for two reasons: wrong credentials, or **email not confirmed** for a newly signed-up account.

---

## Use the same login as when neuro-workflow worked before

**If you had neuro-workflow working before**, use **that exact same email and password** to log in. Do **not** use the account you just created with “Sign up”—that new account may need email confirmation first. So:

- **Log in** with the credentials you used when neuro-workflow worked previously.
- If you don’t remember the password, use “Forgot password” (if available) or ask whoever manages the Supabase project to reset it or confirm your new account (see below).

---

## New account: “Incorrect email address or password” after sign-up

By default Supabase requires **email confirmation** before a new user can sign in. Until the email is confirmed, sign-in fails (often with “Incorrect email address or password”).

### Option A: Supabase Dashboard (if it loads for you)

1. Open **https://app.supabase.com** and sign in.
2. Select the project (API URL `https://rexhbnagqwoygewdiaom.supabase.co`).
3. **Authentication** → **Providers** → **Email**: turn **off** “Confirm email” so new sign-ups can log in without confirming.
4. Or **Authentication** → **Users**: find your user and confirm their email manually.

### Option B: Dashboard doesn’t load (e.g. app.supabase.com blocked)

If **https://app.supabase.com** doesn’t open or work for you:

1. **Ask the person who set up the project** (e.g. your colleague) to either:
   - Turn off “Confirm email” in the project’s Auth settings, or
   - Confirm your user in **Authentication** → **Users**, or
   - Run the script below once with the project’s **service_role** key to confirm your email.

2. **Confirm your user from the command line** (someone with the **service role key** can do this):

   - In the Supabase project: **Project Settings** → **API** → copy the **service_role** key (secret).
   - From the repo root, with that key set only for this command:

     ```bash
     cd gui
     SUPABASE_URL="https://rexhbnagqwoygewdiaom.supabase.co" \
     SUPABASE_SERVICE_ROLE_KEY="<paste-service-role-key-here>" \
     python scripts/confirm_supabase_user_by_email.py your@email.com
     ```

   After the script reports success, you can log in with that email and your password.

---

## Summary

| Situation | What to do |
|-----------|------------|
| You had neuro-workflow working before | **Log in** with that same email and password (don’t use the account you just signed up with). |
| You just signed up and get “Incorrect email or password” | New account needs confirmation: use dashboard (Option A) or ask an admin / run script (Option B). |
| Dashboard (app.supabase.com) doesn’t open | Ask project owner to disable “Confirm email” or confirm your user; or they run `confirm_supabase_user_by_email.py` with the service_role key. |
