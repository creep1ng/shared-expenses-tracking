# ADR 0003: Use cookie-based session authentication

- Status: accepted
- Date: 2026-03-07

## Context

The application is browser-first and will be deployed using a same-parent-domain model with reverse-proxied frontend and backend services.

The system needs secure authentication behavior suitable for workspace-scoped financial data, while keeping the frontend implementation straightforward.

## Decision

The backend will use email/password authentication with backend-issued secure session cookies.

Planned characteristics:

- `HttpOnly` cookies
- `Secure` flag in appropriate environments
- `SameSite=Lax` by default unless a stronger requirement emerges
- server-managed session lifecycle
- Redis-backed session storage by default

The frontend will rely on backend session state rather than storing auth tokens in local storage.

## Rationale

- session cookies fit a browser-first app well
- backend-managed sessions simplify logout, revocation, and permission enforcement
- secure cookies reduce exposure compared with local storage token patterns
- the chosen deployment model makes cookie auth operationally simple

## Consequences

### Positive

- safer default auth posture
- simpler frontend auth handling
- better fit for protected financial flows

### Trade-offs

- requires careful cookie and proxy configuration
- requires session storage strategy and lifecycle management

## Alternatives considered

### JWT stored in local storage

Rejected as the default because it increases exposure in browser environments and shifts more auth responsibility to the client.

### Third-party auth provider as the initial default

Deferred. A third-party provider may be adopted later if requirements justify it, but it is not required for the MVP foundation.
