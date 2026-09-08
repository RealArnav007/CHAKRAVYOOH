# Frontend PRD — Chakravyooh Android Client
### Peer-to-peer emergency messaging that works with no network

**Owner:** Client Lead (Rishabh)
**Team:** IIC 3.0 · Open Innovation · `<add teammate names>`
**Status:** Draft v1.0 · Hackathon build
**Companion docs:** `02_Backend_PRD.md`, `03_API_Contract.md`

---

## 1. Purpose & Scope

The "frontend" here is the **Android application that runs on every phone** — victim, relay, and gateway are the *same app* in different runtime roles. It owns everything that happens on-device with **no connectivity**: detecting an emergency, deciding whether to send, packaging a signed SOS, and relaying it phone-to-phone until it reaches a connected gateway.

This document specifies every screen, state, sensor trigger, and on-device subsystem for the client. It is written so the client can be built **in parallel** with the cloud backend against the shared `03_API_Contract.md` — the client mocks the ingest endpoint, the backend mocks the packet stream.

**In scope (hackathon MVP):** manual SOS + cancel window, mesh discovery/relay/store-carry-forward, gateway detection + forward, GPS attach, local message queue, live mesh/status UI, received-alert view, automatic fall/scream triggers, direct-SMS fallback.

**Out of scope (roadmap, §16):** on-device adaptive-confidence with cached risk maps, ACK propagation UI, missed-check-in timer, payload encryption, iOS, Spray-and-Wait routing.

---

## 2. Roles (same app, three runtime modes)

| Role | When | Responsibility |
|---|---|---|
| **Victim** | Triggers an SOS | Detect → confidence-check → sign → broadcast |
| **Relay** | Receives a packet it hasn't seen | Store, dedup, TTL−−, rebroadcast; carry across gaps |
| **Gateway** | Has connectivity | Forward queued packets to cloud (see `03_API_Contract`) |

Every phone continuously performs all three; the role is determined by state, not a setting.

---

## 3. Screens & States

**3.1 Home / Idle**
Large, unmistakable **SOS button**; a status line ("Mesh active · N peers nearby"); a discreet "I'm safe" state. One-tap to trigger — no menus in an emergency.

**3.2 Sending (cancel window)**
On any trigger, a full-screen **countdown (~5s): "Sending SOS… Cancel"**. Cancel requires a conscious, able user. No cancel → it sends. *(This is where "can't act" quietly becomes "message goes" — TRG-3.)*

**3.3 Relaying / In-Flight**
Shows the SOS is broadcasting: peer count, hop status, "carried by N phones." For a gateway phone, shows "forwarding to responders."

**3.4 Delivered**
Confirmation once an ACK returns through the mesh *(P2)* or a direct-SMS send succeeds.

**3.5 Received Alerts (relay/bystander view)**
A feed of SOSs this phone is relaying — reinforces that the user is part of a life-saving network. Shows coarse location + severity, never sensitive payload if encrypted.

**3.6 Mesh Debug / Demo View**
A live topology visualisation (nodes + links + a packet animating across hops). *This is the demo money-shot surface — invest in it.*

---

## 4. On-Device Subsystems

### 4.1 Trigger System
| ID | Requirement | Priority |
|---|---|---|
| TRG-1 | Manual one-tap SOS | P0 |
| TRG-2 | Cancel window (~5s) before send | P0 |
| TRG-3 | **Send-unless-cancelled** (default = send; no cancel → sends) | P0 |
| TRG-4 | Partial input treated as a trigger, not an abort | P1 |
| TRG-5 | **Fall/impact detection** (accelerometer + gyro) + stillness | P1 |
| TRG-6 | **On-device scream/distress-sound detection** (TFLite audio model) | P1 |
| TRG-7 | No-motion-when-expected | P2 |
| TRG-8 | Missed check-in / dead-man's timer | P2 |

### 4.2 Confidence Engine (client side)
Computes a `confidence` score from fall magnitude, stillness duration, scream-model score, partial text, and no-cancel. Compares against an `effective_threshold`. **Senior call:** for MVP, threshold is a fixed base; adaptive/offline-risk-map tuning (CNF-2/3) is P2 — do **not** let it block the P0 demo. `confidence` and `trigger_type` are written into the packet for backend triage.

### 4.3 Mesh Transport & Routing *(the winning core — build first)*
| ID | Requirement | Priority |
|---|---|---|
| MSH-1 | Peer discovery + P2P transport (Nearby Connections `P2P_CLUSTER`, BLE + Wi-Fi Direct) | P0 |
| MSH-2 | Build + sign the SOS packet (schema per `03_API_Contract` §2) | P0 |
| MSH-3 | Dedup via seen-message cache (`msg_id`) | P0 |
| MSH-4 | Epidemic flooding with TTL hop-limit | P0 |
| MSH-5 | Store-carry-forward — hold when no peer, rebroadcast on new-peer | P0 |
| MSH-6 | Gateway detection → forward queued packets to cloud | P0 |
| MSH-7 | ACK propagation back to origin | P2 |

### 4.4 Delivery Paths
| ID | Requirement | Priority |
|---|---|---|
| SND-1 | On trigger, **broadcast into mesh** (primary route out) | P0 |
| SND-2 | **Direct-SMS fallback** via `SmsManager` (rides cell control channel; often works on weak signal) | P1 |
| SND-3 | Dual attempt — SMS + mesh simultaneously | P1 |
| SND-4 | Attach last-known GPS (FusedLocationProvider) to every packet | P0 |

### 4.5 Local Store
Room/SQLite holds the **store-carry-forward queue** and the **seen-message cache**. Packets expire per TTL/timestamp.

### 4.6 Always-On Service
Automatic triggers (fall/scream) require a **foreground service + persistent notification** — Android kills background sensing otherwise. Request `SEND_SMS`, location, and microphone as runtime permissions with graceful deny-handling.

---

## 5. Design Tokens (emergency-grade UI)

- **Contrast-first:** the SOS action must be legible in panic, bright sun, one-handed. Oversized tap target, high-contrast red primary, no ambiguity.
- **One-tap depth:** the critical path (trigger → send) is reachable from cold-launch in a single action.
- **Calm status, loud action:** idle/relay states are quiet; the send/countdown state is unmissable.
- **Accessibility:** large text, haptic + audible feedback on trigger and on cancel-window countdown.

---

## 6. Acceptance Criteria (MVP / demo)

- Cold-launch → SOS → cancel window → broadcast, in one tap.
- Three phones in **airplane mode** (BT + Wi-Fi on, cellular off): A (out of range of C) → B (bridge) → C; packet arrives at C.
- C is given connectivity → forwards to backend → a real alert is received (see `03_API_Contract`).
- Seen-cache prevents infinite rebroadcast; TTL bounds hops.
- Killing the network mid-relay does not lose the queued packet (store-carry-forward holds it).

---

## 7. Parallel-Build Strategy

The client builds against a **mock ingest** (canned `IngestResult` from `03_API_Contract`) so the mesh + forwarding + UI are testable before the real backend exists. A **mock packet generator** lets the client exercise the relay/dedup path without needing three physical devices during early dev.

---

## 16. Roadmap (post-MVP)

Adaptive confidence + cached offline risk map · ACK propagation UI · missed-check-in dead-man's timer · payload encryption · Spray-and-Wait routing · radio duty-cycling · iOS via custom BLE-GATT.

---

*IIC 3.0 · Open Innovation · v1.0 · pairs with `02_Backend_PRD.md` + `03_API_Contract.md`*
