# Recovering Legacy Projects via the Django Admin

## Background

The Public / Private visibility feature (introduced in PR #15) added a `visibility`
field to `FlowProject` and tightened ownership-based access control. Projects that
existed **before** this change can end up invisible to every user on the
frontend, for one of two reasons:

1. **Backfill defaulted to `Private`.** Depending on which version of the
   migration ran in your deployment, pre-existing rows may have been backfilled
   to `Private` instead of `Public`.
2. **Owner / current user mismatch.** If the deployment switched identity
   providers (or the same provider issued a new `sub` for a user), the legacy
   project's `owner` no longer matches the current logged-in user. A `Private`
   project with an `owner` that nobody can authenticate as is unreachable
   through the API.

In either case the project is "stranded": the row still exists in the database,
but the API filter (`Q(owner=user) | Q(visibility="public")`) excludes it for
every caller.

Switching the project's `visibility` to `Public` via the Django admin makes it
visible again. This page documents that recovery procedure.

> Note: only Public is needed for the project to be **visible**. Editing and
> deleting still require ownership — see "About ownership" below.

---

## Prerequisites

- The web application stack is running via `docker-compose up` (see the project
  README for setup).
- You have shell access to the host running the backend container.
- You know which projects are affected (e.g. users have reported they cannot
  see a workflow they used to own).

---

## Step 1 — Create a Django superuser

The Django admin requires a staff account. If you do not already have one,
create a superuser from inside the backend container.

From the `gui/` directory of the repository on the host:

```bash
docker-compose exec backend python django-project/manage.py createsuperuser
```

You will be prompted for:

- **Username** — anything you like (e.g. `admin`). This is independent from the
  Keycloak / Supabase identity used by end users.
- **Email address** — optional, but recommended.
- **Password** — entered twice. Must satisfy Django's password validators.

On success the command prints `Superuser created successfully.`

> If you have already created a superuser previously and forgotten the
> password, you can reset it from inside the container:
>
> ```bash
> docker-compose exec backend python django-project/manage.py changepassword <username>
> ```

---

## Step 2 — Open the Django admin

The admin is served from the backend on port `3000` under the `/admin/` path.

- Local development: <http://localhost:3000/admin/>
- Deployed environments: `https://<your-backend-host>/admin/`

Log in with the superuser credentials from Step 1. You should land on the
Django admin index page listing the installed apps.

> The admin is **not** the same site as the React frontend (which runs on
> `5173` in development). Do not log in there with Keycloak / Supabase — use
> the Django superuser credentials on the `/admin/` page directly.

---

## Step 3 — Open the FlowProject list

On the admin index page, under the **Workflow** app, click **Flow projects**.

You will see a table of all projects in the database, including legacy rows
that may be invisible to the regular frontend. The default columns are
`Name`, `Owner`, `Is active`, `Created at`, `Updated at`. The `Visibility`
column is **not** shown here, but it is editable on each row's detail page.

---

## Step 4 — Edit a project's visibility

For each project you need to recover:

1. Click the project's **Name** in the list to open its change form.
2. Locate the **Visibility** field. It is a dropdown with two values:
   - `Private`
   - `Public`
3. Select **`Public`**.
4. (Optional) If you also want to re-assign ownership to the user who should
   now be able to edit and delete the project, change the **Owner** field by
   typing in the user lookup or using the magnifying-glass picker.
5. Click **SAVE** at the bottom of the page.

Repeat for each affected project.

> If there are many projects to convert, consider whether a one-off shell
> command is more appropriate than clicking through each one. That approach is
> intentionally not documented here to avoid accidental bulk mutations —
> contact a maintainer if you need it.

---

## Step 5 — Verify on the frontend

1. Open the React frontend (`http://localhost:5173/` in development, or your
   deployed URL) and log in **as a regular end user** (via Keycloak / Supabase
   — not the Django superuser).
2. Confirm the previously invisible project now appears in the project list.
3. If the user is the new owner you set in Step 4, verify they can also edit
   and delete the project. If you left the original (or empty) owner in
   place, the project should be visible and runnable, but the edit / delete
   actions should be disabled for non-owners.

---

## About ownership

`visibility` and `owner` control different things:

| State | Visible to non-owner | Editable by non-owner | Deletable by non-owner |
| ----- | -------------------- | --------------------- | ---------------------- |
| Private + no owner / different owner | No | No | No |
| Public + no owner / different owner | **Yes** | No | No |
| Private + owner is current user | Yes | Yes | Yes |
| Public + owner is current user | Yes | Yes | Yes |

So flipping a stranded project to `Public` is enough for **anyone** to see and
run it, but only the owner can modify or delete it. If you also want to hand
control of the project to a specific user, update the **Owner** field in the
same change form (Step 4).

---

## Notes

- `visibility` is a `CharField` backed by `TextChoices`, not a boolean. Its
  database values are the lowercase strings `"private"` and `"public"`. The
  admin presents them via the dropdown labels `Private` and `Public`.
- The `Is active` flag is a separate concern (soft-delete). A project must
  have `Is active = True` to appear at all; setting visibility on an inactive
  project has no effect on the frontend until you also re-activate it.
- This procedure does not require any code changes. The change form already
  exposes the `Visibility` field because `FlowProjectAdmin` does not restrict
  the form's fields.
