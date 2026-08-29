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
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="Quotation API")


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
    subtotal: float
    tax: float
    grand_total: float


@app.post("/generate-quotation", response_model=QuotationResponse)
def generate_quotation(req: QuotationRequest):
    """
    Placeholder implementation.

    Replace this stub with:
      - a call to the Anthropic API (ANTHROPIC_API_KEY env var is already
        wired up in render.yaml) to parse req.request_text into structured
        items,
      - a lookup against your product catalog (brand/model/part number/price),
      - pricing + tax calculation,
      - and return the assembled quotation.
    """
    return QuotationResponse(
        customer_name=req.customer_name,
        line_items=[],
        subtotal=0.0,
        tax=0.0,
        grand_total=0.0,
    )
