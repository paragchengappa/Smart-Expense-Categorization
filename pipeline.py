import pdfplumber
import re
from supabase import create_client

# Paste your credentials here
SUPABASE_URL = "https://bpkwwwsctogbomsrizmt.supabase.co"
SUPABASE_KEY = "sb_publishable_dPF3gE09KYwNKMDT6uhG1A_lHc3EBAe"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Categorizer rule engine
def get_category(item_name):
    item = item_name.lower()
    if any(k in item for k in ['atta', 'butter', 'oil', 'salt', 'milk', 'bread', 'biscuit']):
        return "Groceries"
    elif any(k in item for k in ['silk', 'chocolate', 'shirt', 'pants']):
        return "Shopping"
    elif any(k in item for k in ['paracetamol', 'crocin', 'syrup']):
        return "Healthcare"
    return "Miscellaneous"

def process_pdf(pdf_path):
    print(f"Processing {pdf_path}...")
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

    lines = text.split("\n")
    merchant = lines[0] if lines else "Unknown Merchant"
    
    gstin_match = re.search(r'GSTIN:\s*([0-9A-Z]{15})', text)
    gstin = gstin_match.group(1) if gstin_match else "N/A"
    
    date_match = re.search(r'Date:\s*(\d{2}-\d{2}-\d{4})', text)
    inv_date = date_match.group(1) if date_match else "2025-10-12"
    if inv_date and "-" in inv_date:
        d, m, y = inv_date.split("-")
        inv_date = f"{y}-{m}-{d}"

    # Extract table items
    items = []
    for line in lines:
        match = re.search(r'^(.*?)\s+(\d+)\s+(\d+\.\d{2})\s+(\d+\.\d{2})$', line.strip())
        if match:
            desc, qty, price, total = match.groups()
            items.append({
                "item_description": desc.strip(),
                "quantity": int(qty),
                "price": float(price),
                "total_price": float(total),
                "category": get_category(desc.strip())
            })

    grand_total = sum(item["total_price"] for item in items)

    # Insert Master Invoice Record into Supabase
    inv_res = supabase.table("invoices").insert({
        "merchant_name": merchant,
        "gstin": gstin,
        "invoice_date": inv_date,
        "grand_total": grand_total
    }).execute()

    invoice_id = inv_res.data[0]["id"]

    # Link & Insert Line Items
    for item in items:
        item["invoice_id"] = invoice_id
    
    supabase.table("invoice_items").insert(items).execute()
    print(f"✅ Extracted & Pushed to Supabase! Invoice ID: {invoice_id}")

if __name__ == "__main__":
    # Loop through receipt_sample_1.pdf to receipt_sample_5.pdf
    for i in range(1, 6):
        file_name = f"receipt_sample_{i}.pdf"
        print(f"Starting extraction for {file_name}...")
        process_pdf(file_name)