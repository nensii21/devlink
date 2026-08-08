# DevLink Security Documentation

## Password Screening (#855)

Composition rules alone are a weak defence. `Password1!`, `Welcome123!` and
`Qwerty123!` all satisfy "8 characters, upper, lower, digit, symbol" and all
appear near the top of every credential-stuffing wordlist. NIST SP 800-63B
recommends screening candidate passwords against known-bad values rather than
relying on composition, so `validate_password` now runs three additional checks
after the structural ones.

### 1. Local blocklist

`app/core/password_blocklist.py` holds an in-repo list of the most commonly
observed passwords. Candidates are normalised before comparison:

| Input             | Normalised | Rejected |
| :---------------- | :--------- | :------- |
| `password`        | `password` | yes      |
| `P@ssw0rd`        | `password` | yes      |
| `Password2025!`   | `password` | yes      |
| `Welcome123!`     | `welcome`  | yes      |

Normalisation lowercases, applies Unicode NFKD folding, strips trailing digits
and punctuation, then undoes common leetspeak substitutions. That means one
blocklist entry covers a whole family of decorated variants, so the list stays
small enough to read.

### 2. Personal information

A password that contains the user's own username or email local-part is
rejected. `alexrivera` picking `Alex.Rivera2025!` is on the first page of any
targeted guess list. Tokens shorter than four characters are ignored — a short
identifier would otherwise match nearly everything — and the email *domain* is
not considered, since every user shares it.

### 3. Have I Been Pwned

The long tail is covered by the HIBP range API using k-anonymity:

1. SHA-1 the candidate password.
2. Send **only the first five hex characters** of the digest.
3. HIBP returns every suffix it holds under that prefix — several hundred.
4. Match our suffix against that list locally.

The password never leaves the process, and neither does its full hash. Requests
set `Add-Padding: true` so every response contains a similar number of entries
and an observer cannot infer anything from the response size. Range responses
are cached for 24 hours.

**This check fails open.** A timeout, connection error or 5xx from HIBP is
logged and treated as "no reason to reject". An outage at a third party must
never become an outage of our signup form.

### Where it applies

Registration, password change, and password reset. Each passes the account's
username and email so the personal-information check has context.

### Configuration

| Setting                     | Default                              | Purpose                                            |
| :-------------------------- | :----------------------------------- | :------------------------------------------------- |
| `ENABLE_PASSWORD_BLOCKLIST` | `true`                               | Local blocklist and personal-information checks     |
| `ENABLE_HIBP_CHECK`         | `true` (`false` under pytest)        | HIBP range lookup                                   |
| `HIBP_API_URL`              | `https://api.pwnedpasswords.com/range` | Range API endpoint                                |
| `HIBP_TIMEOUT_SECONDS`      | `3.0`                                | Per-request timeout                                 |
| `HIBP_MIN_BREACH_COUNT`     | `5`                                  | Occurrences before a password is rejected           |
| `HIBP_CACHE_TTL_SECONDS`    | `86400`                              | How long a range response is cached                 |

`HIBP_MIN_BREACH_COUNT` is above 1 deliberately: single-occurrence entries in
the corpus are often artefacts rather than passwords in active circulation.

`ENABLE_HIBP_CHECK` defaults off under pytest so the suite never depends on a
third party being reachable; the behaviour itself is covered with a mocked
transport in `tests/test_password_screening.py`.

### Error messages

Rejection messages state the category ("too common", "appeared in a known data
breach") and never echo the submitted password back to the client.

---

## Suspicious Login Detection System (#584)

DevLink evaluates all authentication attempts (both successful and failed) in real time to detect suspicious login patterns and protect user accounts against unauthorized access, credential stuffing, and brute force attacks.

### Detection Signals

1. **New Device (`NEW_DEVICE`)**:
   - Compares the client user-agent / device type against historical successful logins recorded for the user in the past 30 days.

2. **New Browser (`NEW_BROWSER`)**:
   - Evaluates the browser family (Chrome, Firefox, Safari, Edge, etc.) against known browsers previously used by the account holder.

3. **Unusual Location (`UNUSUAL_LOCATION`)**:
   - Detects login attempts from IP addresses that differ from the user's past 30-day login history.

4. **Multiple Failed Logins (`MULTIPLE_FAILED_LOGINS`)**:
   - Triggers when 3 or more failed password authentication attempts occur within a 15-minute window for a specific account or IP address.

5. **Rapid Login Attempts (`RAPID_LOGIN_ATTEMPTS`)**:
   - Flags accounts experiencing 2 or more login attempts within a 5-second window.

### Automated Responses

- **Security Alert Notification**: Immediately generates an urgent in-app/email security alert to the user detailing the login attempt, client IP, device info, and triggered detection signals.
- **Immutable Audit Logging**: Records an immutable audit log entry (`AuditAction.SUSPICIOUS_LOGIN_ATTEMPT`) with full request context metadata for security auditing.

## Secrets and Environment Files

### Never commit a `.env`

`backend/.env.example` and `frontend/.env.example` are the templates and belong
in the repository. The `.env` files themselves do not — they carry real
credentials, and once one is committed it is in the history permanently.

Adding a path to `.gitignore` **does not untrack a file git already knows
about**. `backend/.env` sat in the index for months underneath a `.gitignore`
that listed `.env` and looked like it covered the case. If you find a tracked
environment file:

```bash
git rm --cached backend/.env     # untracks it, keeps your local copy
git commit -m "chore: untrack backend/.env"
```

Two things enforce this now:

- `.github/workflows/tracked-files.yml` fails any PR that tracks a `.env` (at
  any depth, `.example` excluded), a developer scratch script, or a file named
  `gitignore` without its leading dot. It inspects the index directly, because
  that is the thing `.gitignore` cannot fix.
- `.pre-commit-config.yaml` refuses the commit locally, and `detect-private-key`
  catches a key pasted into any file.

### What was in the tracked `backend/.env`

For the record, since "a committed .env" sounds worse than this one was. The
`SECRET_KEY` in it was the placeholder
`CHANGE_THIS_TO_A_LONG_RANDOM_SECRET_KEY_AT_LEAST_64_CHARACTERS`, and every API
key and OAuth secret was an empty string. **No rotation was required.**

The one real credential was a developer's local Postgres password inside
`DATABASE_URL`. Local-only, but people reuse passwords, so it is worth changing.

The other consequence was quieter and affected everyone: pydantic-settings
loads `backend/.env` automatically, so a tracked one overrides `config.py` on
every machine and in CI. `SEARCH_RATE_LIMIT` read `60/minute` repository-wide
while the declared default was `30/minute`, and a test asserted the former.

### Rotating a leaked `SECRET_KEY`

If a **real** `SECRET_KEY` is ever committed, this is the procedure.

`SECRET_KEY` signs JWTs (`app/core/config.py`). Anyone who can read a leaked
value can mint tokens that every deployment still running it will accept.
Removing the file from `HEAD` does not help — the value stays in the history,
and in every clone and fork. **Rotation is the fix; untracking only stops it
recurring.**

For each environment, in order:

1. Generate a new value:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

   It must be at least 32 characters — `Settings.SECRET_KEY` enforces that.

2. Set `SECRET_KEY` in that environment's secret store. Never in a tracked file.

3. Restart the backend. Every access and refresh token signed with the old key
   stops verifying, so **all users are signed out**. Plan it accordingly.

4. Consider clearing the `refresh_tokens` table. The rows are already useless
   after the key changes; removing them keeps the active-session views honest.

Rotate the other credentials that shared the file — `DATABASE_URL`,
`REDIS_URL`, and any OAuth client secrets — on the same pass. They were exposed
by the same commit.

### Reporting

Do not open a public issue for a suspected key leak. Follow the process in
[SECURITY.md](../SECURITY.md).
