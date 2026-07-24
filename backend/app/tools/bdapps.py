"""bdapps CaaS (Charging as a Service) — SANDBOX SIMULATION.

Mirrors the request/response shape of the bdapps TAP CaaS direct-debit API
(https://dev.bdapps.com/API_Documentation/bdapps_tap_api.html) so the judge
can see a complete checkout flow: charge request -> operator response ->
balance deduction -> receipt. Clearly labeled simulation; no real charge.
"""
import random
import time

_BALANCES: dict[str, float] = {}
_START_BALANCE = 500.0


def bdapps_checkout(subscriber_number: str, amount_bdt: float, description: str) -> dict:
    amount = round(float(amount_bdt), 2)
    balance = _BALANCES.get(subscriber_number, _START_BALANCE)

    request_payload = {
        "applicationId": "APP_000001 (sandbox)",
        "password": "***redacted***",
        "externalTrxId": f"AGRI{int(time.time())}{random.randint(100, 999)}",
        "subscriberId": f"tel:{subscriber_number}",
        "paymentInstrumentName": "Mobile Account",
        "amount": f"{amount:.2f}",
        "currency": "BDT",
        "description": description,
    }

    if amount > balance:
        response_payload = {
            "statusCode": "E1308",
            "statusDetail": "Insufficient balance in subscriber account",
            "internalTrxId": None,
        }
        receipt = None
    else:
        balance = round(balance - amount, 2)
        _BALANCES[subscriber_number] = balance
        response_payload = {
            "statusCode": "S1000",
            "statusDetail": "Success",
            "internalTrxId": f"BDAPPS{random.randint(10_000_000, 99_999_999)}",
            "timeStamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        receipt = {
            "charged_bdt": amount,
            "description": description,
            "remaining_operator_balance_bdt": balance,
        }

    return {
        "mode": "SANDBOX SIMULATION (no real charge — mirrors bdapps CaaS API shape)",
        "request": request_payload,
        "response": response_payload,
        "receipt": receipt,
    }
