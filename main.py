"""
AI-Powered Quotation Generation System - API skeleton.

This is a minimal, working FastAPI app so the Render Blueprint has
something real to build and deploy. Expand /generate-quotation to:
  1. Parse the natural-language request with Claude
  2. Match items against your product catalog
  3. Apply pricing rules
  4. Return a structured quotation (and/or render a PDF)
"""

import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from anthropic import Anthropic

app = FastAPI(title="Quotation API")

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ---------------------------------------------------------------------------
# Product catalog (placeholder).
# Replace/extend this with your real catalog — brand, model, part number,
# unit price. Keep the "NP" prefix convention and GCC part numbers as needed.
# ---------------------------------------------------------------------------
PRODUCT_CATALOG = [
    {"name": "NP HP LaserJet Pro M404dn", "part_number": "W1A53A#B19", "unit_price": 850.00},
    {"name": "NP HP LaserJet Pro M428fdw", "part_number": "W1A30A#B19", "unit_price": 1450.00},
    {"name": "NP Canon imageCLASS MF3010", "part_number": "5252B004AA", "unit_price": 420.00},
    {"name": "NP Epson EcoTank L3250", "part_number": "C11CJ67501", "unit_price": 380.00},
    {"name": "NP Ricoh Aficio MP 2014", "part_number": "MP2014-GCC", "unit_price": 1200.00},
    {"name": "NP Konica Minolta Bizhub 227", "part_number": "KM227-GCC", "unit_price": 2100.00},
]

TAX_RATE = 0.05  # adjust to your local VAT rate


@app.get("/", response_class=HTMLResponse)
def home():
    """Basic landing page so the root URL isn't blank."""
    return """
    <html>
        <head><title>Quotation API</title></head>
        <body style="font-family: sans-serif; max-width: 600px; margin: 60px auto;">
            <h1>Quotation API is running ✅</h1>
            <p>This is the backend for the AI-powered quotation generator.</p>
            <ul>
                <li><a href="/health">/health</a> — service health check</li>
                <li><a href="/docs">/docs</a> — interactive API docs (try /generate-quotation here)</li>
            </ul>
        </body>
    </html>
    """


@app.get("/health")
def health():
    """Used by Render's health check to confirm the service is alive."""
    return {"status": "ok"}


class QuotationRequest(BaseModel):
    request_text: str          # e.g. "5 HP LaserJet printers for a Doha client, urgent"
    customer_name: str | None = None


class QuotationLineItem(BaseModel):
    product_name: str
    part_number: str
    quantity: int
    unit_price: float
    line_total: float


class QuotationResponse(BaseModel):
    customer_name: str | None
    line_items: list[QuotationLineItem]
    unmatched_requests: list[str] = []
    subtotal: float
    tax: float
    grand_total: float


def parse_request_with_claude(request_text: str) -> list[dict]:
    """
    Send the customer's request + our catalog to Claude and get back
    structured matches: which catalog product each request line refers to,
    and the requested quantity. Anything Claude can't confidently match
    is returned with product_name = null.
    """
    catalog_list = "\n".join(
        f"- {p['name']} (part number: {p['part_number']})" for p in PRODUCT_CATALOG
    )

    prompt = f"""You are helping match a customer's quotation request against a product catalog.

CATALOG:
{catalog_list}

CUSTOMER REQUEST:
"{request_text}"

For each product the customer is asking about, match it to the closest catalog item and
extract the requested quantity. If a request doesn't clearly match any catalog item, set
"matched_name" to null and put the customer's original phrase in "raw_text".

Respond with ONLY a JSON array (no other text, no markdown fences), in this exact shape:
[
  {{"matched_name": "NP HP LaserJet Pro M404dn", "quantity": 5, "raw_text": "5 HP LaserJet printers"}},
  {{"matched_name": null, "quantity": 2, "raw_text": "2 unknown scanners"}}
]
"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = "".join(
        block.text for block in response.content if block.type == "text"
    ).strip()

    # Claude sometimes wraps JSON in ```json fences despite instructions — strip if present.
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Could not parse AI response into structured items.")


@app.post("/generate-quotation", response_model=QuotationResponse)
def generate_quotation(req: QuotationRequest):
    matches = parse_request_with_claude(req.request_text)

    catalog_by_name = {p["name"]: p for p in PRODUCT_CATALOG}
    line_items: list[QuotationLineItem] = []
    unmatched: list[str] = []

    for match in matches:
        matched_name = match.get("matched_name")
        quantity = match.get("quantity") or 1

        if matched_name and matched_name in catalog_by_name:
            product = catalog_by_name[matched_name]
            unit_price = product["unit_price"]
            line_items.append(
                QuotationLineItem(
                    product_name=product["name"],
                    part_number=product["part_number"],
                    quantity=quantity,
                    unit_price=unit_price,
                    line_total=round(unit_price * quantity, 2),
                )
            )
        else:
            unmatched.append(match.get("raw_text", "unrecognized item"))

    subtotal = round(sum(item.line_total for item in line_items), 2)
    tax = round(subtotal * TAX_RATE, 2)
    grand_total = round(subtotal + tax, 2)

    return QuotationResponse(
        customer_name=req.customer_name,
        line_items=line_items,
        unmatched_requests=unmatched,
        subtotal=subtotal,
        tax=tax,
        grand_total=grand_total,
    )
