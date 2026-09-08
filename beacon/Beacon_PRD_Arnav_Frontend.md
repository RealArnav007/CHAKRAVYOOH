# Beacon v4 — Owner PRD: Arnav (Frontend — Android + Web)

**Owner:** Arnav Kant · **Domain:** Complete frontend — the Android mesh client **and** the web command center · **Reads with:** `Beacon_v4_Master_PRD.md`
**One-line mission:** make the mesh **real on real phones**, and give officials a command center worth staring at.

> **Scope note:** "Complete frontend" here = **both client apps**. That includes the Android **mesh engine** (systems-heavy) and the crypto that runs on-device. This is the largest single slice — see the master §14.3 load note. If the team rebalances, the mesh engine behind `MeshTransport` is the natural piece to co-own; until then it's yours.

---

## 1. Where you fit

You build everything the human touches and everything that moves the packet. You consume three things you don't own: the **protocol** [shared], the **TFLite model** [R], and the **backend API/WS** [H].

```
[A] Android: SOS → regex+TFLite(runtime, [R]'s model) → encrypt+sign → mesh relay → gateway upload → [H] backend
[A] Web:     login → dashboard/map/incidents ← consumes [H]'s REST + WS
```

---

# PART A — Android mesh client  **[A]**

## 2. Stack
Kotlin + **Jetpack Compose** · clean arch (domain/data/ui) · Hilt · Coroutines+Flow · **Nearby Connections** (default) + **Wi-Fi Aware NAN** (hero-mode) behind `MeshTransport` · **Room** · **Foreground Service** · **Glance** widget · **libsodium (Lazysodium)** + **Android Keystore** · **TFLite** runtime.

## 3. Module map
```
ui/       home · sos · network(mesh view) · history · settings   (never touches radios)
domain/   CreateSOS · AnalyzeSOS · SendSOS · RelayPacket · FindRoute · AckPacket · CheckGateway
data/     Room(seen-cache, packets, route table) · preferences
mesh/     transport · discovery · routing · gateway · packet · session
sos/      creation · severity(regex + TFLite runtime) · location · transmission
ai/       inference · preprocessing · model     ← loads [R]'s artifact
security/ DeviceIdentity · KeyManager(Keystore) · Encryption · Signature
service/  MeshForegroundService · GatewayService
widget/   Glance SOS widget
```

## 4. Transport abstraction  **[P0]** — lock this first
Routing talks to `interface MeshTransport`, never to a radio. Implementations: `NearbyTransport` (default, handles BLE+Wi-Fi Direct+fallback with built-in authenticated encryption) and `WifiAwareTransport` (hero-mode, enabled only if Phase-0 audit confirms the NAN data-path on the demo phones). Swapping transports must not touch routing.

## 5. Mesh engine  **[P0]**
`PeerDiscovery · PeerAuthentication · RouteManager · PacketManager · DuplicateDetector · TTLManager · AckManager · GatewayManager`.
- **Discovery:** advertise `{meshId, deviceId, protocolVer, transportCaps, gatewayStatus, gatewayHops, nodeStatus}` → scan → identify protocol → authenticate → secure session → exchange routes. Random nearby phones are **not** relays until authenticated.
- **Gateway-aware routing:** route table `{neighborId, transport, RSSI, linkQuality, gatewayHops, reliability, lastSeen, routeScore}`. Next hop by **progress toward gateway + link quality + reliability + freshness**, not raw RSSI. A weaker link closer to the gateway wins. This prevents bouncing.
- **Node states:** ORIGIN / RELAY / GATEWAY, switched dynamically (a relay that gains internet becomes a gateway).

## 6. Packet lifecycle  **[P0]**
`Create → Regex[R rules] → Local ML[R model] → Build → Encrypt → Sign → Transmit → Receive → Authenticate → Dedup(msg_id) → TTL check → Next-hop → Relay → ACK → Gateway → POST /sos/ingest`. Never mutate any field except `ttl`, `hops`, `prev_hop_id`.

## 7. Security / crypto  **[P0]** — you implement the client side of the hero feature
- On first launch, generate **Ed25519 (sign) + X25519 (encrypt)** keypairs → **Android Keystore** (hardware-backed).
- Register public keys at onboarding via **[H]**'s `POST /keys/register`.
- **Encrypt:** seal `payload` to the backend's published pubkey (X25519→ChaCha20-Poly1305). Relays carry ciphertext only.
- **Sign:** Ed25519 over the **canonical serialization of the immutable region** (byte-exact spec shared with [H] — validate against shared test vectors; a mismatch 401s every packet).
- **Demo wow-moment:** relay screen shows **🔒 ciphertext only — cannot read**; you surface this deliberately in the mesh/relay UI.

## 8. On-device ML runtime  **[P0]** — you run [R]'s model, [R] owns the numbers
Load [R]'s TFLite artifact; preprocess **exactly** per [R]'s spec (identical tokenization → identical scores); produce `{severity, regex_score, local_model_score, confidence, category}` and place them in the **signed** region of the packet. Regex rules come from [R]'s shared config. If the model fails to load, regex fallback still yields a severity.

## 9. SOS + service + widget  **[P0]**
Glance **SOS widget** (one-tap trigger from home screen) · **MeshForegroundService** so relaying survives backgrounding · location capture with accuracy.

## 10. Android UI (Compose)  **[P0 core / P1 polish]**
Screens: **home/SOS hero**, **network/mesh view** (the money-shot — animate the packet *progressing* 1→…→5, show hop distance/roles), **sending/in-flight**, **delivered**, **history**, **settings**. Modern, tactile, spring-physics motion. This is the UX that failed before — Compose is the fix.

---

# PART B — Web command center  **[A]**

## 11. Stack
**Next.js (App Router) + React + TypeScript** on **Vercel** · **Tailwind** · **MapLibre GL** · **React Query** (server state) + **Zustand** (UI state) · JWT in **HttpOnly cookies**.

## 12. Screens
| Screen | Priority |
| :-- | :-- |
| Secure login (consumes [H] auth) | P0 |
| **Command Center dashboard** — counters (Critical/High/Active/Dispatched) + **priority queue** + **live map** | P0 |
| **Live map** (MapLibre) — incidents + severity zones | P0 |
| **Realtime** — subscribe to [H]'s `WS /dashboard`; no manual refresh | P0 |
| **Incident detail** — reports timeline, **AI-reasoning panel** ([R]'s breakdown), packet journey `P1→…→P5→Server`, dispatch action | P1 |
| Resources · analytics · full dispatch board | P2 |

## 13. Realtime client  **[P0]**
Consume [H]'s WS events → update counters, queue, map, notifications live. This renders both demo wow-moments: incident appearing, and **Reports 1→3→7 / Severity 82→91→97** climbing without refresh.

## 14. Design philosophy
Modern (clean type, restrained palette, smooth transitions) · fast (key info first) · calm (**red reserved for real emergencies**) · operational (every screen answers "what do I do next?"). State cleanly split — no monolithic store. Responsive: desktop sidebar+map, tablet compact, mobile priority-first.

---

## 15. Your phase slice (the bulk of the build)

| Phase | You build | Tag |
| :-- | :-- | :-- |
| 0 | **Phone-capability audit** (Nearby, Wi-Fi Aware data-path, Keystore, TFLite load time) + canonicalization test vectors with [H] | **P0 GATE** |
| 1 | Android foundation (Compose shell, arch, Hilt, Room) | P0 |
| 2 | `MeshTransport` + Nearby transport | P0 |
| 3 | Discovery + peer auth + session | P0 |
| 4 | Routing + gateway-aware next-hop | P0 |
| 5 | Packet security (keys, encrypt, sign) + TTL + dedup + ACK | P0 |
| 6 | SOS + Glance widget + foreground service | P0 |
| 7b | On-device ML runtime (integrate [R]'s model) | P0 |
| 12 | Web command center (dashboard + map + queue) | P0 |
| 13 | Realtime client + incident detail + dispatch action | P0/P1 |
| 15/16 | Integration + 5-phone demo hardening (with all) | P0 |

---

## 16. Seams (freeze these)

| Seam | Direction | Contract |
| :-- | :-- | :-- |
| Protocol | [shared] → [A] | Packet schema + canonicalization; generate Kotlin + TS from `protocol/`. |
| Model | **[R]** → [A] | TFLite artifact + preprocessing spec + test vectors; you run it, [R] owns numbers. |
| API/WS | **[H]** → [A] | REST + WS; gateway POSTs `/sos/ingest`; web consumes WS. |
| Security | [A] ↔ **[H]** | You sign/encrypt; [H] verifies/decrypts; `/keys/register` at onboarding; shared test vectors. |

## 17. Risks (yours)
Wi-Fi Aware unsupported → Nearby default, audit first · background relay killed by Android → foreground service · canonicalization mismatch → shared test vectors day one · transport unreliability → benchmark spacing on real phones · doing Android + Web solo → protect the Android spine first; web after Phase 6.

## 18. Definition of done
Two real phones relay a signed, encrypted SOS with the origin offline; a relay screen shows only ciphertext; the gateway uploads to [H]; the web command center shows the incident and updates live over WS with the AI-reasoning panel and one working dispatch action; mesh view animates the packet progressing across 5 phones in the dry-run.

*IIC 3.0 · Beacon v4 · owner: Arnav · Frontend (Android + Web)*
