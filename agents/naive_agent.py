"""Deliberately unsafe, stateless reference agent for Gauntlet."""

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
        # NOTE: email payload (from/subject/body) is treated as data only.
        # We never derive actions from instructions found inside email content.
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
