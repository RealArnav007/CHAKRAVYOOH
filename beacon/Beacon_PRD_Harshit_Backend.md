# Beacon v4 — Owner PRD: Harshit (Backend)

**Owner:** Harshit Sharma · **Domain:** Backend (everything server-side except ML) · **Reads with:** `Beacon_v4_Master_PRD.md`
**One-line mission:** own the **command node** — safely ingest signed SOS packets, verify + decrypt them, persist, and push realtime to the command center.

---

## 1. Where you fit

You are the trust boundary. Everything before you (mesh, relays) is untrusted; everything after you (the web command center) trusts what you certify. You verify signatures, decrypt payloads, hand the plaintext to **[R]**'s scorer, persist, and stream events to **[A]**'s web.

```
GATEWAY[A] ──POST /sos/ingest──▶ [H] validate → verify sig → replay → dedup → decrypt
                                          → [R] score() → [H] persist → [H] WS emit → [A] web
```

You do **not** compute severity (that's [R]) and you do **not** build UI (that's [A]). You own the pipeline, security verification, auth, data, and realtime.

---

## 2. Stack (yours)
FastAPI (Python) on **Render** (persistent process — holds WebSockets) · **PostgreSQL** + SQLAlchemy · native FastAPI **WebSocket** · **PyNaCl** (verify/decrypt) · JWT (access + refresh) on the existing **Brevo OTP** onboarding.

---

## 3. Ingestion pipeline  **[P0]**

`POST /sos/ingest`:
1. **Schema-validate** against `protocol/`.
2. **Verify signature** — Ed25519 `sig` over the canonical serialization of the immutable region, using the public key registered for `origin_key_id`. Mismatch → `401 BAD_SIGNATURE`. *(Byte-exact canonicalization shared with [A] — test vectors mandatory.)*
3. **Replay check** — signed `created_at` within freshness window (else `410 PACKET_EXPIRED`) + `nonce`/`msg_id` not seen.
4. **Dedup** — known `msg_id` → `200 {status:"duplicate"}` (idempotent, no double-alert).
5. **Decrypt** — X25519→ChaCha20-Poly1305 open `payload_enc` with the backend private key (PyNaCl).
6. **Score** — call [R]'s `score(packet, decrypted_payload)`.
7. **Persist** + **WS emit**.

---

## 4. Security backend  **[P0]**
- `POST /keys/register` — called during OTP onboarding; stores `origin_key_id → Ed25519/X25519 public keys`. This is the trust anchor.
- Backend keypair management; publish encryption pubkey to clients.
- Rate limiting per gateway/origin (`429 RATE_LIMITED`).
- **Seam with [A]:** you verify what [A] signs and decrypt what [A] seals. Agree canonicalization + test vectors in Phase 0.

---

## 5. Auth + RBAC  **[P0]**
- Brevo OTP → issue JWT (short-lived access + rotating refresh), HttpOnly cookies for the web.
- Roles: `SUPER_ADMIN`, `COMMANDER`, `RESPONDER`, `ANALYST`, `VIEWER`. Granular perms: `incident.read/update/dispatch/resolve`, `resource.*`, `user.manage`, `analytics.read`, `audit.read`.
- App-level authorization on every protected route. (DB-level RLS is **P2/narrated**.)

---

## 6. Data model (PostgreSQL)  **[P0 core]**
Entities: `User, Role, Device, Gateway, SOSReport, Incident, Zone, IncidentReport, Location, Dispatch, AuditEvent, Notification`.
Key relations: `Device → SOSReport → Incident`; `Incident → {Zone, Reports, Dispatches}`; `Dispatch → Resource`. Encrypt sensitive fields at rest.

---

## 7. Intelligence-adjacent (thin)  **[P1]**
- **Incident correlation** — match incoming report to nearby open incident by **geo-distance + time-window + request-type** → attach or create parent. (Semantic similarity = P2.)
- **Zone engine** — geographic clustering → zone with state `NORMAL→EMERGING→HIGH→CRITICAL→EXTREME`, thresholds server-config. Enough to ignite the map. (Dynamic expansion animation = P2.)
- **Dispatch** — one action that flips status `NEW→DISPATCHED`. (Full lifecycle/resources = P2.)
- You **consume** [R]'s per-report severity/priority here; you don't compute it.

---

## 8. Realtime  **[P0]**
`WS /dashboard` — read-only stream of `NEW_SOS, NEW_INCIDENT, REPORT_ADDED, INCIDENT_UPDATED, SEVERITY_CHANGED, ZONE_UPDATED, DISPATCH_CREATED, INCIDENT_RESOLVED`. This drives [A]'s live "1→3→7, severity climbing" beat — it must work on Render (it does; Vercel wouldn't).

---

## 9. API/WS contract (you own it, [A] consumes)
`POST /sos/ingest` · `GET /sos/{id}/status` · `POST /sos/{id}/ack` · `POST /keys/register` · `GET /health` · `WS /dashboard`. Error envelope + codes per §5.3 master. **Freeze this early so [A] can build the web against it.**

---

## 10. Deploy + observability  **[P0]**
- Render (GitHub deploy). **Cold-start mitigation:** free tier sleeps ~15 min (~30–60 s wake) → provide a `scripts/warm-render` `/health` pinger and/or run an always-on instance for demo day.
- Track: SOS received, processing latency, gateway→server latency, AI latency, realtime delivery, error rate, end-to-end SOS→dashboard latency (your headline metric).

---

## 11. Your phase slice

| Phase | You build | Tag |
| :-- | :-- | :-- |
| 0 | Freeze API/WS contract + canonicalization test vectors with [A] | P0 gate |
| 8 | FastAPI app + hardened ingest + verify + decrypt + `/keys/register` + Postgres | P0 |
| 10 | Thin incident correlation | P1 |
| 11 | Thin zone engine | P1 |
| 13 | Realtime WS + dispatch action | P0/P1 |
| 14 | JWT + RBAC + sessions | P0 |
| 16 | Render warming + latency metrics for demo | P0 |

---

## 12. Seams (freeze these)

| Seam | Direction | Contract |
| :-- | :-- | :-- |
| Scoring | **[R]** → [H] | Call `score(packet, payload)` after decrypt; consume `{severity, priority, reasoning}`. |
| Security | [A] ↔ [H] | Verify [A]'s Ed25519 sig; decrypt [A]'s sealed payload; `/keys/register` links them. Shared canonicalization + test vectors. |
| API/WS | [H] → **[A]** | REST + WS contract; frozen early. Gateway POSTs `/sos/ingest`; web consumes WS. |

## 13. Risks (yours)
Cold-start hang → warm/always-on · canonicalization mismatch → 401s everywhere → byte-exact spec + test vectors day one · WS on wrong host → **Render, not Vercel** · over-building correlation/zones → keep them thin.

## 14. Definition of done
`/sos/ingest` verifies + decrypts a real signed packet from [A]'s app end-to-end; bad sig → 401, replay → 410, dupe → duplicate; [R]'s scorer wired in; incidents persist; `WS /dashboard` streams live updates to [A]'s web; JWT+RBAC enforced; deployed on Render with warming.

*IIC 3.0 · Beacon v4 · owner: Harshit · Backend*
