# bdapps API — Complete Agent Reference
Source: official "BDApps API Guide" v1.1.3 (hSenid Mobile / Robi, 2019).
Purpose: everything an agent needs to implement bdapps SMS, USSD, CAAS
(Charging-as-a-Service) and OTP. For the AgriSense hackathon, the scoring
target is the CAAS checkout flow (Section 5) in sandbox mode.
NOTE: this guide is from 2019; the hackathon links the current TAP doc at
https://dev.bdapps.com/API_Documentation/bdapps_tap_api.html — verify field
names there if a call fails with E1312 (invalid request).

---

## 1. Platform fundamentals

- Base URL: `https://developer.bdapps.com`
- All services are **HTTP POST** with `Content-Type: application/json` (both ways).
- **Auth = body credentials, not headers.** Every request carries:
  - `applicationId` — e.g. `"APP_000027"` (32 chars, given at provisioning)
  - `password` — 32-char API key/hash given at provisioning (this IS the secret; keep in `.env`)
- **MSISDN format:** `"tel: 8801XXXXXXXXX"` — the `tel:` prefix is required.
  Samples show both `tel:88018...` and `tel: 88018...` (with space); E1325 = wrong format,
  expected `"tel: 8801812345678"`. Numbers may be RETURNED MASKED depending on app type.
- **Currency:** only `"BDT"`. Amounts are **strings with up to 2 decimals**, e.g. `"8.25"`.
- **Success signal:** HTTP 200 is not enough — check body `statusCode == "S1000"`.
  Anything else is an error (codes in Section 7), possibly still delivered over HTTP 200.
- **Directions:** MT (Mobile Terminated) = your app → bdapps → phone (you call them).
  MO (Mobile Originated) = phone → bdapps → **your app's callback endpoint**
  (they call you; you must reply `{"statusCode":"S1000","statusDetail":"Success"}`).
- `version` param: optional in requests (`"1.0"`); omitted → validated against latest.

## 2. Endpoint catalog

| # | Service | Method+Path | Direction |
|---|---------|-------------|-----------|
| 1 | SMS Send | POST `/sms/send` | app → bdapps |
| 2 | SMS Receive | (bdapps POSTs to your URL) | bdapps → app |
| 3 | SMS Delivery Report | (bdapps POSTs to your URL) | bdapps → app |
| 4 | USSD Send | POST `/ussd/send` | app → bdapps |
| 5 | USSD Receive | (bdapps POSTs to your URL) | bdapps → app |
| 6 | CAAS Query Balance | POST `/caas/balance/query` | app → bdapps |
| 7 | CAAS Payment Instruments | POST `/caas/list/pi` | app → bdapps |
| 8 | CAAS **Direct Debit** | POST `/caas/direct/debit` | app → bdapps |
| 9 | OTP Request | POST `/subscription/otp/request` | app → bdapps |
| 10 | OTP Verify | POST `/subscription/otp/verify` | app → bdapps |

---

## 3. SMS

### 3.1 Send (`POST /sms/send`)
Request parameters:

| Param | Type | M/O | Notes |
|-------|------|-----|-------|
| applicationId | String | M | |
| password | String | M | |
| message | String | M | over-limit messages are auto-split |
| destinationAddresses | String[] | M (≥1) | `["tel:8801812345678"]`; special value `"tel: all"` = broadcast to app's subscribed base |
| sourceAddress | String | O | must be a provisioned alias, else E1331 (or omit → default shortcode) |
| deliveryStatusRequest | Enum "0"/"1" | O | 1 = send me a Delivery Report later; default 0 |
| encoding | Enum | O | `0`=Text (default), `16`=Bengali, `240`=Flash SMS, `245`=Binary (hex content) |
| binaryHeader | Hex string | O* | MANDATORY if encoding is Flash or Binary |
| chargingAmount | String 2dp | O | variable-charging apps only, BDT |
| version | String | O | "1.0" |

Sample request:
```json
{
  "applicationId": "APP_000027",
  "password": "10d8769c825f4aad0c511dfe3de3f121",
  "message": "Sample Message",
  "destinationAddresses": ["tel:8801812345678"]
}
```

Response fields: `statusCode`, `statusDetail`, `requestId`, `version`,
`destinationResponses[]` — one entry per address, each with
`address`, `timeStamp` (yyyymmddhhmmss), `messageId` (keep it — matches later
delivery report), `statusCode`, `statusDetail`.

### 3.2 Receive (MO SMS — bdapps calls YOUR endpoint)
Incoming JSON: `message`, `requestId`, `applicationId`,
`sourceAddress` ("tel: ..."), `encoding`, `version`.
Your endpoint must respond: `{"statusCode":"S1000","statusDetail":"Success"}`.

### 3.3 Delivery Status Report (bdapps calls YOUR endpoint)
Incoming JSON: `destinationAddress`, `timeStamp`, `requestId`,
`deliveryStatus` ∈ {DELIVERED, EXPIRED, DELETED, UNDELIVERABLE, ACCEPTED,
UNKNOWN, REJECTED}. Doc states format "yyMMddHHmm" but samples show longer —
parse defensively. Match to your send via requestId/messageId.
Reply `{"statusCode":"S1000","statusDetail":"Success"}`.

---

## 4. USSD

Session-based: bdapps' USSD Gateway assigns a `sessionId` at session start;
the SAME sessionId must be echoed in every message of that session.

### ussdOperation enum (who assigns what)
- `mo-init` — bdapps → you, subscriber dialed in (session start)
- `mo-cont` — bdapps → you, subscriber's next input in an open session
- `mt-init` — you → bdapps, app initiates a session
- `mt-cont` — you → bdapps, app continues session (menu screen, keeps it open)
- `mt-fin`  — you → bdapps, final message, ends the session

### 4.1 Send (`POST /ussd/send`)
Request: `applicationId` (M), `password` (M), `message` (M — the menu text,
newlines allowed), `sessionId` (M), `ussdOperation` (M), `destinationAddress`
(M, "tel: ..."), `encoding` (O: `440`=plain ASCII, `16`=Bengali),
`chargingAmount` (O), `version` (O).
Response: `statusCode`, `requestId`, `statusDetail`, `version`.

### 4.2 Receive (MO USSD — bdapps calls YOUR endpoint)
Incoming: `message` (user's input, e.g. "1"), `ussdOperation` (mo-init/mo-cont),
`sessionId`, `requestId`, `encoding`, `applicationId`, `sourceAddress`, `version`.
Reply `{"statusCode":"S1000","statusDetail":"Success"}` as the ack, then drive
the conversation by calling `/ussd/send` with `mt-cont` (next menu) or
`mt-fin` (goodbye screen).

---

## 5. CAAS — Charging as a Service  ⟵ hackathon checkout lives here

### 5.1 Query Balance (`POST /caas/balance/query`)
Request:

| Param | M/O | Notes |
|-------|-----|-------|
| applicationId, password | M | |
| subscriberId | M | "tel: 8801812345678" |
| paymentInstrumentName | M | e.g. `"Mobile Account"` |
| accountId | O | e.g. "8801812345678" |
| currency | O | only "BDT" |

Response: `statusCode`, `statusDetail`,
`chargeableBalance` (string, 2dp — prepaid: remaining balance; postpaid:
credit limit minus outstanding), `accountStatus` (e.g. "0"),
`accountType` ("PREPAID"/"POSTPAID").

### 5.2 Get Payment Instrument List (`POST /caas/list/pi`)
Request: `applicationId`, `password`, `subscriberId`, `type` (O: sync|async|all, default all).
Response: `statusCode`, `statusDetail`,
`paymentInstrumentList`: `[{"name":"Mobile Account","type":"sync"}]`.

### 5.3 Direct Debit (`POST /caas/direct/debit`) — the actual charge
Request:

| Param | M/O | Notes |
|-------|-----|-------|
| applicationId, password | M | |
| externalTrxId | M, ≤32 | **app-generated, UNIQUE per transaction** (reuse → E1337 duplicate); your reconciliation key |
| subscriberId | M | "tel: ..." |
| paymentInstrumentName | M | "Mobile Account" |
| amount | M | string, 2dp, BDT — e.g. "5" or "8.25" |
| currency | O | "BDT" |
| accountId | O | |

Sample request:
```json
{
  "externalTrxId": "25609",
  "amount": "5",
  "applicationId": "APP_000010",
  "password": "8f57d2e8de06e6f2d6ee5da6107d0a4f",
  "subscriberId": "tel: 8801812345678",
  "paymentInstrumentName": "Mobile Account"
}
```
Sample response:
```json
{
  "statusCode": "S1000",
  "timeStamp": "2013-08-01T08:43:34.344+05:30",
  "externalTrxId": "25609",
  "statusDetail": "Request was successfully processed",
  "internalTrxId": "913080108430074"
}
```
Response fields: `externalTrxId` (echo), `internalTrxId` (gateway's unique txn
id — put it on the receipt), `referenceId` (O, 8 digits, for external charging
menus), `timeStamp` (ISO-8601), `statusCode`, `statusDetail`.

---

## 6. OTP (MSISDN verification / subscription)

### 6.1 Request OTP (`POST /subscription/otp/request`)
Request: `applicationId` (M), `password` (M), `subscriberId` (M, "tel: ..."),
`applicationHash` (O, first 11 chars of base64 app hash — Android SMS Retriever),
`applicationMetaData` (O): `{client: MOBILEAPP|WEBAPP, device, os, appCode}`.
Response: `statusCode`, `statusDetail`, **`referenceNo`** (15 chars — store it),
`version`.

### 6.2 Verify OTP (`POST /subscription/otp/verify`)
Request: `applicationId`, `password`, `referenceNo` (from 6.1), `otp` (6 chars).
Response: `statusCode`, `statusDetail`,
`subscriptionStatus` ("REGISTERED"/"UNREGISTERED"), `version`,
`subscriberId` — **masked** tel: id; use this masked id for all subsequent
requests for that user.

---

## 7. Status & error codes (complete)

Success: **S1000** — processed successfully.

Non-retryable errors:

| Code | Meaning / agent action |
|------|------------------------|
| E1313 | Auth failed (bad applicationId/password/inactive SP) → fix credentials |
| E1303 | Caller IP not provisioned for this app → whitelist server IP in bdapps portal |
| E1312 | Invalid request (missing/malformed field) → check schema against current doc |
| E1309 | SMS service not allowed for this app |
| E1311 | MT SMS not enabled (NCS config) |
| E1315 | Requested service not found / inactive |
| E1317 | MSISDN invalid or not allowed |
| E1325 | Address format invalid — expected "tel: 8801812345678" |
| E1328 | Charging operation not allowed (NCS config) |
| E1331 | sourceAddress not a provisioned alias → omit it or use provisioned value |
| E1334 / E1335 | Message / advertisement too long |
| E1337 | Duplicate request (reused externalTrxId) → generate fresh id |
| E1341 | Request failed for all destinations |
| E1342 | MSISDN blacklisted for this app |
| E1343 | MSISDN not whitelisted — **dev/sandbox apps only accept whitelisted test numbers**; add your SIM in the portal |
| E1308 | Permanent charging error (e.g. insufficient balance) → surface to user |
| E1601 | Unexpected system error |

Retryable errors:

| Code | Meaning |
|------|---------|
| E1318 | TPS limit exceeded → throttle + retry with backoff |
| E1319 | Daily transaction limit exceeded → retry tomorrow |
| E1326 | Insufficient balance (listed retryable — treat as user-facing failure, retry only after top-up) |
| E1602 | Delivery failed, retry |
| E1603 | Temporary system error, retry |
| E1850 / E1851 / E1852 | OTP invalid / expired / max attempts |

Glossary: NCS=Network Capability Service, MO=Mobile Originated,
MT=Mobile Terminated, MSISDN=subscriber number, SLA=Service Level Agreement.

---

## 8. AgriSense integration playbook (the 10-point checkout)

Rubric line: "Successful simulation of the bdapps CaaS API flow
(request/response) during checkout."

**Flow to demo** (e.g. farmer buys the fertilizer plan / pays for inputs):
1. `caas/list/pi` → show "Mobile Account" as payment method (optional step)
2. `caas/balance/query` → show chargeable balance, confirm affordability
3. `caas/direct/debit` with fresh `externalTrxId` (e.g. `AGRI-{timestamp}`)
4. Render receipt: amount BDT, externalTrxId, internalTrxId, ISO timeStamp
5. Log all four request/response pairs in the agent trace panel

**Client design (do this, it saves the demo):**
```python
class BdappsClient:
    def __init__(self, app_id, password, simulate=False): ...
    def query_balance(self, msisdn) -> dict: ...
    def direct_debit(self, msisdn, amount, ext_trx_id) -> dict: ...
```
- `simulate=True` returns realistic canned payloads (S1000, random 15-digit
  internalTrxId, now() as ISO timestamp) so the demo cannot die on network/
  provisioning issues. Declare real-vs-simulated in the README (required).
- Real mode: register app at developer.bdapps.com → get applicationId +
  password → whitelist your test SIM (E1343) and server IP (E1303).

**Gotchas checklist:** tel: prefix on every number · amounts as strings ·
check `statusCode=="S1000"` not HTTP status · unique externalTrxId per charge ·
store internalTrxId for the receipt · credentials in `.env` only.

**Free bonus ideas using the same client:** `sms/send` with `encoding:16`
(Bengali) to push proactive weather alerts ("ভারী বৃষ্টি ৪ দিনের মধ্যে — ইউরিয়া
প্রয়োগ পেছান") = Tier-1 proactive advice + Bengali accessibility in one call.
