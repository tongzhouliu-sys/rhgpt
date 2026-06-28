# Session Seeding (B8 / FR-11 / §12.6)

Web-automation Providers reuse a logged-in browser profile instead of logging in
on every run. You log in **once, locally, in a headed browser**, then ship the
resulting profile directory to the server's persistent Volume. Login state
(cookies / localStorage / IndexedDB) lives inside that directory.

> Profiles are secrets: they grant access to the account. They never enter Git
> (`.gitignore` covers `data/profiles/`), live on a Volume with tight perms
> (700), and are treated as disposable — re-seed if a session expires.

## 1. Log in locally (headed)

Prereqs: a desktop with a display, and `pip install playwright && playwright
install chromium`.

```bash
# profile path MUST match providers.yaml (e.g. chatgpt_web_1.profile)
python scripts/seed_session.py --site chatgpt --profile data/profiles/chatgpt_acc1
```

A real Chrome window opens at the site. Log in fully (including 2FA/captcha),
open a normal chat so the session is established, then return to the terminal
and press Enter. The login state is now saved under `data/profiles/chatgpt_acc1`.

Repeat per account/site (`--site claude`, `--site deepseek`, ...).

## 2. Package the profile

```bash
tar -czf chatgpt_acc1.tgz -C data/profiles chatgpt_acc1
```

## 3. Inject into the Railway Volume

Mount the Volume at `data/profiles/` (so the path matches `providers.yaml`), then
upload and extract the profile into it:

```bash
# from a shell with access to the Volume mount
tar -xzf chatgpt_acc1.tgz -C /data/profiles
chmod -R 700 /data/profiles/chatgpt_acc1
```

The container runs headed-under-Xvfb (§12.2), and `_browser.get_context` opens a
**persistent context** at `data/profiles/chatgpt_acc1`, reusing the seeded login.

## 4. Smoke test

Run the manual E2E (see `tests/e2e/README.md`) driving at least one web Provider
+ one API Provider through `pipelines/round1.yaml`. The web step should produce a
real answer with no login prompt. If a step raises `SessionExpiredError` (logged
as `session_expired`), the profile is stale — re-seed from step 1.

## Notes

- One directory per account; never share a profile across concurrent jobs (the
  Runtime serializes per-profile via the Profile lock, §5.8).
- Rotate/refresh profiles periodically; sessions expire. Keep ≥1 spare account
  per site so a stale session can be swapped quickly.
- API Providers (`gemini_api`, `qwen_api`) need **no** seeding — they use an API
  key from the environment, not a browser profile.
