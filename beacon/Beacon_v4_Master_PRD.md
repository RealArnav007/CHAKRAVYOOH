# Product Requirements Document — Project Beacon v4.0 (Master)

**Project:** Project Beacon — self-organizing, offline-first emergency communication & coordination platform
**Version:** 4.0 · **New repository** (greenfield build) · **Supersedes:** v3.0
**Event:** IIC 3.0 — International Innovation Challenge · Open Innovation track
**Status:** Master build spec — locked stack, spine-frozen, 3-owner division

---

## 0. How to read this document

Two layers, on purpose:

- **SPINE** — the one demo path we build to production quality. This wins.
- **VISION** — the full platform. We *architect* it, *narrate* it as roadmap, and build only the thin slice the demo needs.

Priority tags on every requirement:

| Tag | Meaning |
| :-- | :-- |
| **P0** | Non-negotiable. Demo fails without it. |
| **P1** | Thin slice — convincing minimum, not scale. |
| **P2** | Narrated only. Architected + roadmap slide. **Do not build for the deadline.** |

Ownership tags:

| Tag | Owner | Domain |
| :-- | :-- | :-- |
| **[R]** | **Rishabh** | ML / Intelligence (on-device model + backend severity/priority) |
| **[H]** | **Harshit** | Backend (everything server-side except ML) |
| **[A]** | **Arnav** | Frontend (complete Android client + web command center) |
| **[shared]** | all three | `packages/protocol/` — the frozen contract everyone builds against |

> **Goal hierarchy:** Win the hackathon **first** → strengthen the product **second** → strengthen the patent **third**. Every scope call serves that order.

---

## 1. What Beacon is (one-paragraph pitch)

When disaster knocks out cell towers and internet, phones go dark exactly when people need them most. Beacon turns ordinary Android phones into a **self-healing offline mesh**: a victim's SOS hops phone-to-phone over Wi-Fi Aware/Bluetooth with **no network at all**, until it reaches any one phone that still has internet — which silently forwards it to a cloud command center. On the way, the message is **end-to-end encrypted and signed**, so relay phones physically cannot read or tamper with it. On arrival, on-device + cloud AI grades severity, clusters related reports into incidents, ignites affected zones on a live map, and hands officials a prioritized dispatch queue. **Phone = communicate. Backend = understand. Web = act.**

---

## 2. Final system architecture

```
                     ┌────────────────────────────┐
                     │   OFFICIAL USERS           │  Commanders / Responders
                     └──────────────┬─────────────┘
                                    │ HTTPS + WebSocket (realtime)
                     ┌──────────────▼─────────────┐
                     │   WEB COMMAND CENTER  [A]   │  Next.js + React + Tailwind + MapLibre
                     └──────────────┬─────────────┘
                                    │ Secure REST + WS
                     ┌──────────────▼─────────────┐
                     │   BACKEND  [H] + [R]        │  FastAPI (Render)
                     │   [H] Auth·RBAC·Ingestion·  │
                     │       Sig-verify·Decrypt·   │
                     │       Correlation·Zones·WS  │
                     │   [R] Regex·Groq·Severity·  │
                     │       Priority Engine       │
                     └──────────────┬─────────────┘
                                    │ HTTPS (internet only)
                          ┌─────────▼─────────┐
                          │  GATEWAY PHONE [A] │  Same Beacon APK, has internet
                          └─────────┬─────────┘
                                    │ Wi-Fi Aware / BLE
                     ┌──────────────▼─────────────┐
                     │   OFFLINE MESH  [A]         │  P1→P2→P3→P4→P5
                     │   Routing·TTL·Dedup·        │  E2E encrypted · signed
                     └──────────────┬─────────────┘
                                    │ Wi-Fi Aware / BLE
                              ┌─────▼─────┐
                              │ SOS PHONE │  [A] client · [R] on-device model
                              └───────────┘
```

Any Beacon APK install is a **NODE** that dynamically acts as **ORIGIN**, **RELAY**, or **GATEWAY**.

---

## 3. Locked tech stack

| Layer | Choice | Owner |
| :-- | :-- | :-- |
| Android | **Kotlin + Jetpack Compose** · clean arch · Hilt · Coroutines+Flow | [A] |
| Mesh transport | **Nearby Connections** (default) behind `MeshTransport`; **Wi-Fi Aware NAN** hero-mode | [A] |
| On-device storage | **Room** (seen-cache, packets, route table) | [A] |
| Background/widget | **Foreground Service** + **Glance** SOS widget | [A] |
| On-device ML | **TensorFlow Lite** (<10 MB) + configurable regex | model **[R]** / runtime **[A]** |
| Android crypto | **libsodium (Lazysodium)** · **Android Keystore** | [A] |
| Backend | **FastAPI (Python)** on **Render** | [H] |
| Database | **PostgreSQL** + SQLAlchemy | [H] |
| Realtime | native FastAPI **WebSocket** | [H] |
| Backend crypto | **PyNaCl** (verify/decrypt) | [H] |
| Backend AI | **Groq Llama-3** + regex → Priority Engine | [R] |
| Web | **Next.js (App Router) + React + TS** on **Vercel** | [A] |
| Web libs | **Tailwind** · **MapLibre GL** · **React Query** + **Zustand** | [A] |
| Shared | `packages/protocol/` · **Protobuf** on-wire · JSON REST | [shared] |

---

## 4. Repository structure (new monorepo)

```
beacon/                          # NEW repo
├── apps/
│   ├── android/                 # [A] Kotlin + Compose mesh client
│   └── web/                     # [A] Next.js command center
├── services/
│   └── backend/                 # [H] FastAPI (+ [R] ml modules inside)
│       └── src/ml/              # [R] regex, groq, severity, priority
├── packages/
│   └── protocol/                # [shared] .proto, canonicalization, error codes
├── ml/                          # [R] training, datasets, TFLite export, evaluation
├── docs/                        # architecture / api / protocol / security / demo
├── scripts/                     # seed_admin, warm-render, node-id generator
└── docker-compose.yml
```

---

## 5. The Protocol — single frozen source of truth  **[shared] · [P0] · GATE ZERO**

> **Highest-risk item.** All three build against one schema. It is frozen **once** in Phase 0 and never renamed. One renamed field silently kills delivery.

### 5.1 Mesh Packet (three regions — this split is what makes security work)

**IMMUTABLE — set by origin, signed, never altered by a relay:**
`msg_id` (UUID, dedup key) · `origin_id` · `origin_key_id` (which key signed) · `created_at` (epoch ms) · `nonce` · `lat`,`lon`,`acc` · `trigger_type` · `request_type` · `severity` (info|warn|critical) · `regex_score` (0–100) · `local_model_score` (0–100) · `confidence` (0–1) · `payload_enc` (E2E ciphertext).

**MUTABLE — changes per hop, NOT signed:** `ttl` (−1/hop) · `hops` (+1/hop) · `prev_hop_id`.

**AUTH:** `sig` — Ed25519 over canonical serialization of the immutable region only.

> **Severity vs priority.** Origin ships a *severity assessment* (`severity`+`regex_score`+`local_model_score` [R]) inside the signed region so relays can't inflate it. The **authoritative operational priority is computed by the backend Priority Engine [R]**, never trusted from the wire.

### 5.2 Signing canonicalization — define byte-exact, day one
Canonical bytes = immutable fields in the fixed order above, length-prefixed, concatenated — independent of Protobuf ordering. Documented in `docs/protocol/canonicalization.md`. **[A] signs it, [H] verifies it — shared test vectors required.**

### 5.3 Cloud REST/WS contract (owned by [H], consumed by [A])
`POST /sos/ingest` → validate → **verify sig** → replay check → dedup → **decrypt** → **[R] severity+priority** → persist → **WS emit**.
`GET /sos/{id}/status` · `POST /sos/{id}/ack` · `POST /keys/register` (onboarding) · `GET /health` · `WS /dashboard`.
Errors: `INVALID_PACKET` 422 · `BAD_SIGNATURE` 401 · `MISSING_GATEWAY_ID` 422 · `RATE_LIMITED` 429 · `PACKET_EXPIRED` 410 · `INTERNAL` 500. Duplicate `msg_id` → `200 {status:"duplicate"}`.

---

## 6. Security architecture — hero feature  **[P0]**

**Principle: end-to-end, not hop-by-hop.** Encrypt + sign once at the origin [A]; verify + decrypt only at the backend [H]. Every relay is untrusted dumb transport.

**Two layers:** (1) neighbor/session — Nearby Connections' built-in authenticated encryption [A]; (2) end-to-end — payload sealed X25519→ChaCha20-Poly1305 to backend key, immutable region signed Ed25519 with origin device key [A] → verified/decrypted [H].

**Key lifecycle [A]+[H]:** app generates Ed25519+X25519 on first launch, stored in Android Keystore [A]; public keys registered during Brevo OTP onboarding via `POST /keys/register` [H]; backend publishes its encryption pubkey.

**Threat → mitigation:** relay reads → sealed payload · relay tampers → signature over immutable region incl. severity · replay → `msg_id` dedup + signed `created_at` + `nonce` · spoof flood → sig vs registered key + rate limit · blackhole drop → multipath flood + ACK (resilience, honestly stated).

**Demo-visible wow-moment [A]:** relay screen shows **🔒 ciphertext only — cannot read**; command center shows it decrypted.

---

## 7. Intelligence pipeline — ML & severity  **[R] · [P0 spine / P1 fusion]**

Two tiers, forced by the encryption boundary (encrypted payload → no edge scoring; only origin pre-encryption or cloud post-decryption).

**On-device (origin, offline) [R] model / [A] runtime:** `SOS text → Regex → TFLite classifier → {severity, category, confidence, regex_score, local_model_score}`. Scores ride **inside the signed packet**. Regex = configurable rules [R]; TFLite <10 MB trained on `ml/datasets` [R].

**Cloud (backend, online) [R]:** `decrypted SOS → Regex → Groq (Llama-3) → structured analysis`. **Groq never directly dispatches.** The **Priority Engine [R]** fuses `severity + regex + local_model + Groq + corroboration + location + time + trend` → normalized, **configurable & auditable**.

**AI transparency [R] output → [A] renders:** each incident shows `Regex 88 · Groq 94 · Corroboration +8 · Location +3 · Trend +2`.

---

## 8. Backend spec

| Module | Owner | Priority |
| :-- | :-- | :-- |
| FastAPI app, config, Render deploy, observability | [H] | P0 |
| Ingestion (validate → verify sig → replay → dedup → decrypt) | [H] | P0 |
| Key registration (`/keys/register` at OTP) + PyNaCl verify/decrypt | [H] | P0 |
| Auth (Brevo OTP → JWT access+refresh) + RBAC | [H] | P0 |
| PostgreSQL data model + persistence | [H] | P0 |
| Realtime `WS /dashboard` (event stream) | [H] | P0 |
| **Regex engine + Groq + Severity scoring** | **[R]** | P0 |
| **Priority Engine (fusion)** | **[R]** | P0 |
| AI transparency payload | [R] | P1 |
| Thin incident correlation (geo+time+type) | [H] | P1 |
| Thin zone engine (cluster → state) | [H] | P1 |
| Single dispatch action (status flip) | [H] | P1 |
| Full dispatch lifecycle, resources, analytics, audit UI, RLS, MFA | [H] | **P2 (narrated)** |

**Seam [H]↔[R]:** ingestion, after decrypt, calls a clean internal interface `score(packet, decrypted_payload) → {severity, priority, reasoning}` owned by [R]. [H] never computes severity; [R] never touches transport/auth.

---

## 9. Frontend — Android client  **[A]**

```
apps/android/
├── ui/       home · sos · network(mesh view) · history · settings   (Compose; never touches radios)
├── domain/   CreateSOS · AnalyzeSOS · SendSOS · RelayPacket · FindRoute · AckPacket · CheckGateway
├── data/     Room (seen-cache, packets, route table) · preferences
├── mesh/     transport(MeshTransport→Nearby default / WifiAware hero) · discovery · routing · gateway · packet · session
├── sos/      creation · severity(regex + TFLite runtime) · location · transmission
├── ai/       inference · preprocessing · model   ← loads [R]'s TFLite artifact
├── security/ DeviceIdentity · KeyManager(Keystore) · Encryption · Signature
├── service/  MeshForegroundService · GatewayService
└── widget/   Glance SOS widget
```

Mesh engine [A]: `PeerDiscovery · PeerAuthentication · RouteManager · PacketManager · DuplicateDetector · TTLManager · AckManager · GatewayManager`. Transport abstraction locked early — routing talks to `interface MeshTransport`, never a radio. **Gateway-aware routing:** next hop by *progress toward gateway + link quality + reliability + freshness*, not raw RSSI. Packet lifecycle: `Create → Regex → Local ML → Build → Encrypt → Sign → Transmit → Receive → Authenticate → Dedup → TTL → Next-hop → Relay → ACK → Gateway → Server`.

---

## 10. Frontend — Web command center  **[A]**

```
apps/web/  →  login · dashboard · incidents/[id] · map · dispatch · settings
```

| Screen | Priority |
| :-- | :-- |
| Secure login (JWT/HttpOnly) | P0 |
| Dashboard (counters + priority queue + live map) | P0 |
| Live map (MapLibre): incidents + severity zones | P0 |
| Realtime updates (no refresh) — consumes [H]'s WS | P0 |
| Incident detail (reports, AI-reasoning panel, packet journey, dispatch action) | P1 |
| Resources · analytics · full dispatch board | P2 |

Design: modern, fast, calm (red reserved for real emergencies), operational. State split: server (React Query) / UI (Zustand) / auth — no monolithic store.

---

## 11. Frozen spine (the non-negotiable demo path)

```
Widget → SOS → Regex + Local ML[R] → Encrypt + Sign[A] → Wi-Fi Aware/BLE relay[A] →
Gateway[A] → HTTPS → Backend verify+decrypt[H] → Groq + Regex[R] → Priority[R] →
thin clustering + zone[H] → Realtime dashboard[A] → one Dispatch action[H/A]
```

Cut from the **end** of the vision, never from the spine.

---

## 12. Build phases (dependency-ordered, deadline-flexible)

| Phase | Deliverable | Owner | Tag |
| :-- | :-- | :-- | :-- |
| **0** | Phone-capability audit + **freeze `protocol/`** + repo scaffold | all | **P0 GATE** |
| 1 | Android foundation (Compose, arch, Hilt, Room) | [A] | P0 |
| 2 | `MeshTransport` + Nearby transport | [A] | P0 |
| 3 | Discovery + peer auth + session | [A] | P0 |
| 4 | Routing + gateway-aware next-hop | [A] | P0 |
| 5 | Packet security (keys, encrypt, sign) + TTL + dedup + ACK | [A] | P0 |
| 6 | SOS + Glance widget + foreground service | [A] | P0 |
| 7 | **On-device model** (dataset, train, TFLite export, regex rules) | **[R]** | P0 |
| 7b | On-device ML runtime integration | [A] | P0 |
| 8 | Backend: hardened ingest + verify + decrypt + Postgres | [H] | P0 |
| 9 | **Groq + regex + Priority Engine** | **[R]** | P0 |
| 10 | Thin incident correlation | [H] | P1 |
| 11 | Thin severity zones | [H] | P1 |
| 12 | Web command center (dashboard + map + queue) | [A] | P0 |
| 13 | Realtime + incident detail + dispatch action | [A]/[H] | P0/P1 |
| 14 | JWT + RBAC + sessions | [H] | P0 |
| 15 | Full integration | all | P0 |
| 16 | 5-phone demo hardening (warm Render, spacing, dry-runs) | all | P0 |

---

## 13. Demo — choreography

Five phones, one signed APK (different node IDs): `Node1 SOS → 2 → 3 → 4 → Node5 gateway → Backend → Command Center`.

1. Network forms (mesh view lights up) · 2. **Kill internet on Node 1** · 3. Trigger SOS from widget · 4. Mesh relays 1→…→5 — **Wow A: relay shows 🔒 ciphertext** · 5. Gateway uploads · 6. Backend intelligence (Regex+Groq+location) · 7. **🚨 CRITICAL incident** + AI reasoning · 8. Corroboration — **Wow B: Reports 1→3→7, Severity 82→91→97, live** · 9. Zone ignites on map · 10. Dispatch 🚑/🚒, status flips.

**Hardening (P0):** warm Render before presenting (free tier sleeps ~15 min, ~30–60 s cold start) or use an always-on instance; ≥3 full dry-runs on the real phones in the real room; measure hop success → set spacing from data; keep a recorded backup video.

**Metrics to show:** delivery ≥ target · duplicate relays = 0 · route loops = 0 · gateway discovery ≤ target · dashboard update ≤ target · end-to-end SOS→dashboard latency.

---

## 14. Work division & seam map

### 14.1 Ownership

- **[R] Rishabh — ML / Intelligence.** On-device severity model (train + TFLite export + regex rules + preprocessing spec) and the backend intelligence modules (regex, Groq, severity scoring, Priority Engine, AI-transparency output). Owns severity end-to-end. → *see `Beacon_PRD_Rishabh_ML.md`.*
- **[H] Harshit — Backend.** FastAPI, ingestion pipeline, security verify/decrypt, key registration, auth (OTP→JWT), RBAC, Postgres, thin correlation + zones, dispatch, realtime WS, Render deploy, observability. → *see `Beacon_PRD_Harshit_Backend.md`.*
- **[A] Arnav — Frontend (both clients).** Entire Android app (mesh engine, transport, routing, crypto, Compose UI, on-device ML runtime, foreground service, widget) **and** the Next.js web command center. → *see `Beacon_PRD_Arnav_Frontend.md`.*

### 14.2 The four seams (where people meet — freeze these)

1. **Protocol [shared]** — packet schema + canonicalization. Frozen in Phase 0; all three generate from it.
2. **Severity contract [R]→[A] and [R]→[H]** — [R] hands [A] the TFLite model + preprocessing + the `severity/regex_score/local_model_score` field spec (rides in signed packet); [R] exposes `score(packet, payload)` to [H]'s ingestion.
3. **API/WS contract [H]→[A]** — [H]'s REST + WebSocket is what [A]'s web consumes and the gateway phone POSTs to.
4. **Security seam [A]↔[H]** — [A] signs/encrypts on-device; [H] verifies/decrypts; `POST /keys/register` links them at onboarding; shared canonicalization test vectors.

### 14.3 Honest load note
As divided, **[A] carries the most** (both client apps + mesh + crypto). If the team wants to rebalance, the **Android mesh engine** (transport/routing/gateway) is the natural piece to consider co-owning — it's systems-heavy and self-contained behind `MeshTransport`. Stated division is honored above; this is only a flag.

---

## 15. Top risks

| # | Risk | Mitigation | Owner |
| :-- | :-- | :-- | :-- |
| 1 | Schema drift between apps | Freeze `protocol/` in Phase 0; generate both sides | all |
| 2 | Wi-Fi Aware unsupported on demo phones | Nearby is default; NAN hero-mode only; audit first | [A] |
| 3 | Signature canonicalization mismatch → all 401 | Byte-exact spec day one + shared test vectors | [A]+[H] |
| 4 | Render cold-start hangs first SOS | Warm `/health` / always-on instance | [H] |
| 5 | Model too big/slow on demo phones | <10 MB TFLite, benchmark load time in Phase 0 | [R] |
| 6 | Scope creep rebuilds full vision | Hard freeze to §11 spine; P2 = slides | all |

---

## 16. Patent / IPR alignment

Strengthens the existing filing (applicant: MUJ; inventors: Rishabh Rana, Harshit Sharma, Arnav Kant, Dr. Arpita Baronia). Novel claims to foreground: (1) **E2E authenticated encryption over an untrusted multi-hop phone relay fabric** with severity signals inside the signed region; (2) **on-device offline severity assessment that travels inside the signed packet**, fused with cloud AI in an auditable Priority Engine; (3) **gateway-progress-aware routing** over a heterogeneous Wi-Fi Aware/BLE transport abstraction.

---

*IIC 3.0 · Project Beacon · v4.0 master · new repo · 3-owner · spine-frozen*
