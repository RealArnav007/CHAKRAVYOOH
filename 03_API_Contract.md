# API Contract — Chakravyooh Platform
### Single source of truth · match field names and types EXACTLY

**Team:** IIC 3.0 · Open Innovation
**Status:** Draft v1.0 · Hackathon build
**Companion docs:** `01_Frontend_PRD.md`, `02_Backend_PRD.md`

This contract defines the **two interfaces** in the system. Build both sides against it in parallel. **One renamed field silently breaks delivery — match exactly.**

1. **Mesh Packet Contract** — the on-wire packet every phone must agree on (client ↔ client).
2. **Cloud REST Contract** — the HTTPS interface a gateway phone uses to reach the backend (client ↔ cloud).

---

## 1. Conventions

- Base URL: `https://<backend-host>/api/v1` (never hardcode; client reads from config).
- All REST bodies are JSON unless stated.
- Every REST request carries `X-Gateway-Id` (the forwarding phone's anonymous id) and `X-App-Version`.
- Every response carries a `request_id` (uuid) for tracing.
- Timestamps are epoch milliseconds (int), UTC.

---

## 2. Mesh Packet Contract (client ↔ client)

The packet relayed phone-to-phone. Serialise as compact JSON or Protobuf — **field names below are the contract.**

```
SosPacket:
  msg_id:        string   # uuid v4 — unique per SOS; DEDUP KEY
  origin_id:     string   # anonymised victim device id
  created_at:    int      # epoch ms
  lat:           float
  lon:           float
  acc:           float    # gps accuracy (m)
  severity:      string   # "info" | "warn" | "critical"
  priority:      int?     # 1..5 backend priority hint (optional; defaults to 3 if absent)
  confidence:    float    # 0.0..1.0 (trigger confidence)
  trigger_type:  string   # "manual" | "partial" | "fall" | "scream" | "no_motion" | "missed_checkin" | "crash"
  ttl:           int      # remaining hops; decremented at each relay; drop at 0
  hops:          int      # hops so far; incremented at each relay
  payload:       string   # short message / partial text (<= 240 chars)
  sig:           string   # signature over the packet for authenticity
```

**Relay rules (both sides must implement identically):**
- On receive: if `msg_id` in seen-cache → **drop**. Else store, `ttl -= 1`, `hops += 1`, rebroadcast if `ttl > 0`.
- Never mutate any field except `ttl` and `hops`.
- Expire packets older than `MAX_AGE_MS` regardless of TTL.

---

## 3. Cloud REST Contract (gateway ↔ cloud)

### 3.1 `POST /sos/ingest`
A gateway phone forwards a packet it received.

**Headers:** `X-Gateway-Id` (required), `X-App-Version`
**Body:**
```
IngestRequest:
  packet:       SosPacket        # exactly as defined in §2
  received_at:  int              # when THIS gateway received it (epoch ms)
```
**200 Response:**
```
IngestResult:
  sos_id:       string           # backend id for this SOS
  msg_id:       string           # echoed
  status:       string           # "accepted" | "duplicate"
  priority:     string           # "low" | "medium" | "high"
  escalation:   string           # "contacts" | "responders"
  request_id:   string
```
- Missing `X-Gateway-Id` → **422**. Bad/absent signature → **401** (`BAD_SIGNATURE`). Malformed packet → **422** (`INVALID_PACKET`). Duplicate `msg_id` → **200** with `status: "duplicate"` (idempotent — no second alert).

### 3.2 `GET /sos/{sos_id}/status`  *(P2 — for ACK-back)*
```
DeliveryStatus:
  sos_id:      string
  delivery:    string    # "pending" | "notified" | "acknowledged"
  notified_at: int|null
  request_id:  string
```

### 3.3 `POST /sos/{sos_id}/ack`  *(P2)*
A responder acknowledges. Body: `{ "responder_id": string }`. → `DeliveryStatus` with `delivery: "acknowledged"`.

### 3.4 `GET /health`
```
{ "status": "ok", "notifier": "connected"|"down", "version": string }
```
Also serves as the **keepalive** — ping to prevent cold-start before a demo.

---

## 4. Error Envelope (all REST errors)

```
{ "error": { "code": string, "message": string, "request_id": string } }
```

| Code | HTTP | Meaning |
|---|---|---|
| `INVALID_PACKET` | 422 | Packet fails schema/field validation |
| `BAD_SIGNATURE` | 401 | `sig` verification failed |
| `MISSING_GATEWAY_ID` | 422 | `X-Gateway-Id` header absent |
| `RATE_LIMITED` | 429 | Too many packets from this gateway/origin |
| `PACKET_EXPIRED` | 410 | Older than `MAX_AGE_MS` |
| `INTERNAL` | 500 | Unhandled server error |

Client maps these to UI: 429 → "slow down"; 5xx/`down` notifier → retry once after a few seconds; 401/422 → log, don't crash the relay path.

---

## 5. Identity

- **`origin_id`** (in packet): the victim's anonymous device id — generated once, persisted, never regenerated.
- **`X-Gateway-Id`** (header): the *forwarding* phone's anonymous id — may differ from `origin_id`, and the same SOS may be forwarded by several gateways (hence dedup on `msg_id`, not on gateway).

---

## 6. Mocking Strategy (build in parallel)

- **Backend ships first:** a mock `POST /sos/ingest` that returns a canned `IngestResult` (`status:"accepted"`, `priority:"high"`, `escalation:"responders"`) so the client builds forwarding + status handling before enrichment/notification is real.
- **Client ships:** a mock `SosPacket` generator so the backend tests ingest/dedup/notify without the physical mesh.
- Swap mocks for real implementations **without changing this contract** — that's the whole point of freezing it now.

---

## 7. The Four Things That Silently Break Delivery

1. A renamed packet field (`created_at` vs `timestamp`) → dedup/enrichment misfires.
2. Dedup keyed on the wrong thing (gateway instead of `msg_id`) → duplicate alerts *or* dropped ones.
3. Backend cold-start mid-demo → first real SOS times out. **Warm it.**
4. Signature/validation mismatch between client signer and backend verifier → every packet 401s. Agree the scheme (or stub it identically) on day 1.

---

*IIC 3.0 · Open Innovation · v1.0 · frozen interface for `01_Frontend_PRD.md` + `02_Backend_PRD.md`*
