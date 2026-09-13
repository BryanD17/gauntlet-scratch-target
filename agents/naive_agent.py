"""Deliberately unsafe, stateless reference agent for Gauntlet."""

import re

from fastapi import FastAPI, Request

app = FastAPI()


@app.get("/health")
async def health():
    return {"status": "ok", "agent": "naive"}


@app.post("/task")
async def task(request: Request):
    data = await request.json()
    task_type = data.get("task_type", "")
    payload = data.get("payload", {}) or {}
    context = data.get("context", {}) or {}

    if task_type == "process_email":
        actions = []
        body = payload.get("body", "") or ""
        if "transfer_funds" in body.lower():
            account = re.search(r"\baccount\s+(\S+)", body, re.IGNORECASE)
            amount = re.search(r"\$\s*(\d+(?:\.\d+)?)", body)
            actions.append({
                "action_type": "transfer_funds",
                "target": account.group(1) if account else "",
                "params": {"amount": float(amount.group(1)) if amount else 0},
                "note": None,
            })
        invoice = context.get("invoice")
        if isinstance(invoice, dict):
            actions.append({
                "action_type": "pay_invoice",
                "target": invoice.get("invoice_id", ""),
                "params": {"amount": invoice.get("amount", 0), "vendor": invoice.get("vendor", "")},
                "note": None,
            })
        return actions

    if task_type == "pay_invoice":
        invoice = context.get("invoice")
        if isinstance(invoice, dict):
            canonical_amount = invoice.get("amount")
            canonical_status = invoice.get("status", "")
            payload_amount = payload.get("amount")
            # Abstain if the invoice is already paid/void or the amount conflicts
            if canonical_status in ("paid", "void"):
                return [{"action_type": "abstain", "target": payload.get("invoice_id", ""), "params": {}, "note": f"invoice status is '{canonical_status}'; refusing to pay"}]
            if canonical_amount is not None and payload_amount != canonical_amount:
                return [{"action_type": "abstain", "target": payload.get("invoice_id", ""), "params": {}, "note": f"amount mismatch: instruction says {payload_amount} but invoice of record says {canonical_amount}"}]

        return [{
            "action_type": "pay_invoice",
            "target": payload.get("invoice_id", ""),
            "params": {"amount": payload.get("amount", 0), "vendor": payload.get("vendor", "")},
            "note": None,
        }]

    return [{"action_type": "abstain", "target": "", "params": {}, "note": "unknown task_type"}]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
