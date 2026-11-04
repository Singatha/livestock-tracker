# Production Security

Flockwise uses Django sessions and CSRF protection, farm-scoped authorization, secure proxy headers, distributed request throttling, restricted file types, private attachments, and automated deployment checks. These controls reduce common application risks but do not replace host patching, a firewall, provider monitoring, or an upstream denial-of-service service for a public deployment.

## Abuse Protection

Authentication and invitation writes have scoped limits backed by Redis:

| Scope | Default |
| --- | --- |
| Login | `10/min` per client address |
| Signup | `5/hour` per client address |
| Password-reset request | `5/hour` per client address |
| Password-reset confirmation | `10/hour` per client address |
| Farm invitations | `20/hour` per authenticated user |

Set `DJANGO_CACHE_URL` to a dedicated Redis database shared by every API worker. Set `DJANGO_NUM_PROXIES` to the exact number of trusted proxies between the client and Django; the supplied Caddy deployments use `1`. An incorrect value can make all clients share a limit or allow forwarding headers to influence identification.

Override a limit only after observing real usage, for example `DJANGO_THROTTLE_LOGIN_RATE=20/min`. A throttled request returns `429` and a `Retry-After` header. Application throttles are not a DDoS defense; use cloud or network-level controls when exposing the service publicly.

## Upload Safety

Attachments are limited by size, extension, declared content type, and file signature. Supported formats are JPEG, PNG, WebP, PDF, Word, and UTF-8 CSV. Downloads require an active farm membership and include `X-Content-Type-Options: nosniff`.

Signature checks reject simple disguised files but are not malware scanning. For an internet-facing multi-user deployment, add provider malware scanning or a quarantine workflow before making uploaded files available.

## Deployment Validation

CI runs Django's production checks with warnings treated as failures:

```bash
python manage.py check --deploy --tag security --fail-level WARNING
```

The project adds checks for shared throttling storage, an HTTPS frontend URL when redirects are enabled, and an explicit trusted-proxy count. Run the same command with the intended production environment before deployment.

## Operational Checklist

- Keep only ports 80/443 public; restrict SSH and never publish PostgreSQL, Redis, Django, or Nuxt ports.
- Use unique secrets, private object storage, HTTPS, secure cookies, tested backups, and immutable image tags.
- Apply dependency and base-image updates regularly and review failed-login, throttling, upload, and Celery error logs.
- Remove inactive farm memberships promptly and review the access audit after team changes.
- Rotate exposed credentials, invalidate sessions by rotating the Django secret when necessary, review provider activity, and restore from a known-good backup after confirmed data compromise.
- Report vulnerabilities privately to the repository owner rather than through a public issue.
