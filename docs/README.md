# Flockwise Documentation

This directory records the current product and technical design.

- [Architecture](architecture.md): system context, runtime components, module boundaries, request flows, tenancy, security, and background work.
- [Database design](database-design.md): entity relationships, ownership, constraints, indexes, deletion behavior, and data integrity rules.
- [Observability](observability.md): health endpoints, request correlation, structured logging, optional error reporting, and alert recommendations.
- [Transactional email](email-delivery.md): SMTP configuration, background delivery, retries, verification, and deliverability guidance.
- [MVP specification](mvp.md): original first vertical slice. Some deferred capabilities have since been implemented.
- [ADR 0001](adr/0001-modular-monolith.md): decision to replace the original microservices with a Django and Nuxt modular monolith.

Update these documents when a change affects component responsibilities, trust boundaries, persistent entities, or important domain invariants. Use a new ADR for consequential decisions that need their rationale preserved.
