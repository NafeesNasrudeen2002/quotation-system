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
    {"name": "NP HP Color Laser MFP 178nw", "part_number": "4ZB96A#B19", "unit_price": None},
    {"name": "NP HP Color Laser 150nw", "part_number": "4ZB95A#B19", "unit_price": None},
    {"name": "NP HP Color Laser MFP 179fnw", "part_number": "4ZB97A#B19", "unit_price": None},
    {"name": "NP HP Color LaserJet Pro MFP M182n", "part_number": "7KW54A#B19", "unit_price": None},
    {"name": "NP HP Color LaserJet Pro MFP M183fw", "part_number": "7KW56A#B19", "unit_price": None},
    {"name": "NP HP Color LaserJet Pro M255dw", "part_number": "7KW64A#B19", "unit_price": None},
    {"name": "NP HP Color LaserJet Pro M454dw", "part_number": "W1Y45A#B19", "unit_price": None},
]

TAX_RATE = 0.05  # adjust to your local VAT rate


@app.get("/", response_class=HTMLResponse)
def home():
    """Quotation console — a small internal tool for drafting AI-matched quotations."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Quotation Console — Royce World Trading and Services</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{
    --steel:#2E3944;
    --paper:#ECEEF0;
    --ink:#12181F;
    --amber:#E8A33D;
    --amber-dark:#C9861F;
    --teal:#4C7A6B;
    --line:#C7CDD3;
  }
  *{box-sizing:border-box;}
  body{
    margin:0;
    background:
      repeating-linear-gradient(0deg, rgba(18,24,31,0.025) 0 1px, transparent 1px 28px),
      repeating-linear-gradient(90deg, rgba(18,24,31,0.025) 0 1px, transparent 1px 28px),
      var(--paper);
    color:var(--ink);
    font-family:'Inter', sans-serif;
    min-height:100vh;
  }
  header.nameplate{
    background:var(--steel);
    color:var(--paper);
    padding:28px 24px 22px;
    border-bottom:3px solid var(--amber);
  }
  header.nameplate .brand{
    font-family:'Oswald', sans-serif;
    font-weight:700;
    font-size:clamp(20px, 3vw, 28px);
    letter-spacing:0.04em;
    text-transform:uppercase;
    margin:0;
  }
  header.nameplate .eyebrow{
    font-family:'Oswald', sans-serif;
    font-weight:500;
    font-size:12px;
    letter-spacing:0.22em;
    text-transform:uppercase;
    color:var(--amber);
    margin:6px 0 0;
  }
  main{
    max-width:760px;
    margin:0 auto;
    padding:32px 20px 80px;
  }
  .panel{
    background:#fff;
    border:1px solid var(--line);
    border-radius:2px;
    padding:24px;
    margin-bottom:28px;
  }
  .panel h2{
    font-family:'Oswald', sans-serif;
    font-size:14px;
    letter-spacing:0.14em;
    text-transform:uppercase;
    margin:0 0 16px;
    color:var(--steel);
  }
  label{
    display:block;
    font-size:12px;
    font-weight:600;
    letter-spacing:0.03em;
    text-transform:uppercase;
    color:var(--steel);
    margin-bottom:6px;
  }
  textarea, input[type=text]{
    width:100%;
    font-family:'Inter', sans-serif;
    font-size:15px;
    padding:10px 12px;
    border:1px solid var(--line);
    border-radius:2px;
    background:var(--paper);
    color:var(--ink);
    margin-bottom:18px;
  }
  textarea{ min-height:88px; resize:vertical; }
  textarea:focus, input:focus{
    outline:2px solid var(--amber);
    outline-offset:1px;
  }
  button{
    font-family:'Oswald', sans-serif;
    font-weight:600;
    letter-spacing:0.06em;
    text-transform:uppercase;
    font-size:14px;
    background:var(--amber);
    color:var(--ink);
    border:none;
    padding:12px 22px;
    border-radius:2px;
    cursor:pointer;
  }
  button:hover{ background:var(--amber-dark); }
  button:disabled{ opacity:0.6; cursor:progress; }
  button:focus-visible{ outline:2px solid var(--steel); outline-offset:2px; }

  #result{ display:none; position:relative; }
  #result.visible{ display:block; }

  .stamp{
    position:absolute;
    top:18px; right:18px;
    font-family:'Oswald', sans-serif;
    font-weight:700;
    font-size:13px;
    letter-spacing:0.18em;
    color:var(--amber-dark);
    border:2px solid var(--amber-dark);
    border-radius:3px;
    padding:4px 10px;
    transform:rotate(-7deg);
    opacity:0;
    transition:opacity 0.25s ease, transform 0.25s ease;
  }
  #result.visible .stamp{ opacity:1; transform:rotate(-7deg) scale(1); }
  @media (prefers-reduced-motion: reduce){
    .stamp{ transition:none; }
  }

  table{ width:100%; border-collapse:collapse; margin-top:6px; }
  th, td{
    text-align:left;
    padding:8px 6px;
    border-bottom:1px solid var(--line);
    font-size:14px;
  }
  th{
    font-family:'Oswald', sans-serif;
    font-size:11px;
    letter-spacing:0.08em;
    text-transform:uppercase;
    color:var(--steel);
  }
  td.num, th.num{ text-align:right; font-family:'IBM Plex Mono', monospace; font-size:13px; }
  td.mono{ font-family:'IBM Plex Mono', monospace; font-size:13px; }

  .totals{ margin-top:14px; text-align:right; font-family:'IBM Plex Mono', monospace; }
  .totals div{ margin:4px 0; font-size:14px; }
  .totals .grand{ font-size:17px; font-weight:600; color:var(--steel); border-top:1px solid var(--line); padding-top:8px; margin-top:8px; }

  .note{
    margin-top:16px;
    padding:10px 12px;
    background:rgba(76,122,107,0.09);
    border-left:3px solid var(--teal);
    font-size:13px;
    color:var(--ink);
  }
  .note strong{ color:var(--teal); }

  footer{
    text-align:center;
    font-size:12px;
    color:var(--steel);
    opacity:0.6;
    padding:20px;
  }
</style>
</head>
<body>

<header class="nameplate">
  <p class="brand">Royce World Trading and Services</p>
  <p class="eyebrow">Quotation Console — GCC Catalog</p>
</header>

<main>
  <section class="panel">
    <h2>New Request</h2>
    <label for="customerName">Customer (optional)</label>
    <input type="text" id="customerName" placeholder="e.g. Al Fardan Group">
    <label for="requestText">What do they need?</label>
    <textarea id="requestText" placeholder="e.g. 5 HP Color LaserJet Pro M454dw and 2 HP Color Laser 150nw, urgent"></textarea>
    <button id="submitBtn" onclick="generate()">Generate Quote →</button>
  </section>

  <section class="panel" id="result">
    <span class="stamp">Quote</span>
    <h2>Draft Quotation</h2>
    <table>
      <thead>
        <tr><th>Item</th><th>Part #</th><th class="num">Qty</th><th class="num">Unit Price</th><th class="num">Line Total</th></tr>
      </thead>
      <tbody id="lineItems"></tbody>
    </table>
    <div class="totals">
      <div>Subtotal: <span id="subtotal"></span></div>
      <div>Tax: <span id="tax"></span></div>
      <div class="grand">Total: <span id="grandTotal"></span></div>
    </div>
    <div id="notes"></div>
  </section>
</main>

<footer>Internal tool · draft quotations only, review before sending to customer</footer>

<script>
async function generate(){
  const btn = document.getElementById('submitBtn');
  const requestText = document.getElementById('requestText').value.trim();
  const customerName = document.getElementById('customerName').value.trim();
  if(!requestText){ return; }

  btn.disabled = true;
  btn.textContent = 'Matching…';

  try{
    const res = await fetch('/generate-quotation', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({request_text: requestText, customer_name: customerName || null})
    });
    if(!res.ok){ throw new Error('Request failed'); }
    const data = await res.json();

    const tbody = document.getElementById('lineItems');
    tbody.innerHTML = '';
    data.line_items.forEach(item => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${item.product_name}</td><td class="mono">${item.part_number}</td>
        <td class="num">${item.quantity}</td><td class="num">${item.unit_price.toFixed(2)}</td>
        <td class="num">${item.line_total.toFixed(2)}</td>`;
      tbody.appendChild(tr);
    });

    document.getElementById('subtotal').textContent = data.subtotal.toFixed(2);
    document.getElementById('tax').textContent = data.tax.toFixed(2);
    document.getElementById('grandTotal').textContent = data.grand_total.toFixed(2);

    const notes = document.getElementById('notes');
    notes.innerHTML = '';
    if(data.unmatched_requests && data.unmatched_requests.length){
      notes.innerHTML += `<div class="note"><strong>Not in catalog:</strong> ${data.unmatched_requests.join(', ')}</div>`;
    }
    if(data.missing_price_items && data.missing_price_items.length){
      notes.innerHTML += `<div class="note"><strong>No price set for:</strong> ${data.missing_price_items.join(', ')}</div>`;
    }

    document.getElementById('result').classList.add('visible');
  } catch(e){
    alert('Could not generate the quotation. Check the server logs.');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate Quote →';
  }
}
</script>
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
    missing_price_items: list[str] = []
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
    missing_price: list[str] = []

    for match in matches:
        matched_name = match.get("matched_name")
        quantity = match.get("quantity") or 1

        if matched_name and matched_name in catalog_by_name:
            product = catalog_by_name[matched_name]
            unit_price = product["unit_price"]

            if unit_price is None:
                missing_price.append(product["name"])
                continue

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
        missing_price_items=missing_price,
        subtotal=subtotal,
        tax=tax,
        grand_total=grand_total,
    )
