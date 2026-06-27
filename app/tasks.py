import os
import time
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
from app.celery_worker import celery
from app.database import SessionLocal
import json
from app.models import Job, Transaction, JobSummary 

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")


def normalize_date(date_value):
    try:
        return pd.to_datetime(date_value, dayfirst=True).strftime("%Y-%m-%d")
    except Exception:
        return None


def clean_transactions(df):
    df["category"] = df["category"].fillna("Uncategorised")
    df["currency"] = df["currency"].astype(str).str.upper()
    df["status"] = df["status"].astype(str).str.upper()
    df["amount"] = df["amount"].astype(str).str.replace("$", "", regex=False)
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["date"] = df["date"].apply(normalize_date)
    df = df.drop_duplicates()
    return df


def detect_anomalies(df):
    anomalies = []
    for account in df["account_id"].unique():
        account_data = df[df["account_id"] == account]
        median_amount = account_data["amount"].median()
        threshold = median_amount * 3

        anomaly_rows = account_data[account_data["amount"] > threshold]
        for _, row in anomaly_rows.iterrows():
            anomalies.append({
                "txn_id": row["txn_id"],
                "account_id": row["account_id"],
                "merchant": row["merchant"],
                "amount": float(row["amount"]),
                "reason": "Amount exceeds 3x account median"
            })
    return anomalies


def detect_currency_anomalies(df):
    domestic = ["Swiggy", "Ola", "IRCTC"]
    anomalies = []
    
    # Vectorized filtering instead of iterrows for speed
    currency_mask = (df["currency"] == "USD") & (df["merchant"].isin(domestic))
    currency_anomaly_rows = df[currency_mask]
    
    for _, row in currency_anomaly_rows.iterrows():
        anomalies.append({
            "txn_id": row["txn_id"],
            "merchant": row["merchant"],
            "currency": row["currency"],
            "reason": "Domestic merchant using USD"
        })
    return anomalies


def classify_transactions_batch(transactions):
    prompt = f"""
You are a financial transaction classifier.

For each transaction assign EXACTLY ONE category.

Allowed categories:

- Food
- Shopping
- Travel
- Transport
- Utilities
- Cash Withdrawal
- Entertainment
- Other

Return ONLY valid JSON.

Example:

{{
    "Swiggy":"Food",
    "Amazon":"Shopping",
    "Netflix":"Entertainment"
}}

Transactions:

{json.dumps(transactions, indent=2)}
"""

    retries = 3

    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()

            # Gemini sometimes wraps JSON in ```json ... ```
            text = text.replace("```json", "").replace("```", "").strip()

            return json.loads(text)
        except Exception as e:
            print(f"Batch Gemini Error (Attempt {attempt+1}): {e}")
            if attempt < retries-1:
                time.sleep(2**attempt)

    return {}


def generate_ai_summary(clean_df, anomalies):
    transactions = []

    for _, row in clean_df.iterrows():
        transactions.append({
            "merchant": str(row["merchant"]),
            "amount": float(row["amount"]) if not pd.isna(row["amount"]) else 0.0,
            "currency": str(row["currency"]),
            "category": str(row["category"]),
            "status": str(row["status"])
        })

    prompt = f"""
You are a financial analyst.

Analyze the following transactions.

Transactions:
{json.dumps(transactions, indent=2)}

Detected anomalies: {len(anomalies)}

Return ONLY valid JSON in this format:

{{
    "narrative": "2-3 sentence financial summary.",
    "risk_level": "Low"
}}

Risk level must be exactly one of:

Low
Medium
High

Do not return markdown.
Do not return explanation.
Return only JSON.
"""

    retries = 3

    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()

            text = text.replace("```json", "")
            text = text.replace("```", "")
            text = text.strip()

            return json.loads(text)
        except Exception as e:
            print(f"Summary Generation Error (Attempt {attempt+1}): {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)

    return {
        "narrative": "Unable to generate AI summary.",
        "risk_level": "Unknown"
    }


@celery.task
def process_csv(filepath, job_id):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        job.status = "processing"
        db.commit()

        raw_df = pd.read_csv(filepath)
        clean_df = clean_transactions(raw_df)

        anomalies = detect_anomalies(clean_df)
        currency_anomalies = detect_currency_anomalies(clean_df)

        # Convert anomaly txn_ids to a set for O(1) lookups instead of O(N) loops
        anomaly_txn_ids = {str(a["txn_id"]) for a in anomalies}

        transactions_to_create = []

        total_inr = 0.0
        total_usd = 0.0
        merchant_spend = {}

        # -----------------------------
        # Batch Gemini Classification
        # -----------------------------
        merchant_batch = []
        unique_merchants = clean_df["merchant"].dropna().unique()

        for merchant in unique_merchants:
            sample = clean_df[clean_df["merchant"] == merchant].iloc[0]
            merchant_batch.append({
                "merchant": merchant,
                "amount": float(sample["amount"]),
                "currency": str(sample["currency"]),
                "status": str(sample["status"]),
                "notes": "" if pd.isna(sample["notes"]) else str(sample["notes"])
            })

        merchant_cache = classify_transactions_batch(merchant_batch)
        
        for _, row in clean_df.iterrows():
            merchant = str(row["merchant"])
            amount = float(row["amount"]) if not pd.isna(row["amount"]) else 0.0
            currency = str(row["currency"])

            # 1. Financial aggregation calculations
            if currency == "INR":
                total_inr += amount
            elif currency == "USD":
                total_usd += amount

            # Storing total spend grouped purely by merchant name
            merchant_spend[merchant] = merchant_spend.get(merchant, 0) + amount

            # 2. Category classification using batch cache lookup
            predicted_category = merchant_cache.get(merchant, "Other")

            # 3. Queue up Transaction object
            transaction = Transaction(
                job_id=job.id,
                txn_id=str(row["txn_id"]),
                date=str(row["date"]),
                merchant=merchant,
                amount=str(row["amount"]),
                currency=currency,
                status=str(row["status"]),
                category=predicted_category,
                account_id=str(row["account_id"]),
                notes="" if pd.isna(row["notes"]) else str(row["notes"]),
                is_anomaly="Yes" if str(row["txn_id"]) in anomaly_txn_ids else "No"
            )
            transactions_to_create.append(transaction)

        # Bulk save all transactions for much faster database I/O
        db.bulk_save_objects(transactions_to_create)

        # 4. Update job metrics
        job.row_count_raw = len(raw_df)
        job.row_count_clean = len(clean_df)
        job.anomaly_count = len(anomalies)
        job.currency_anomaly_count = len(currency_anomalies)
        job.status = "completed"

        # 5. Extract top merchants safely separating currency formats
        top_merchants_list = sorted(
            merchant_spend.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]

        # 6. Generate Summary
        ai_summary = generate_ai_summary(clean_df, anomalies)

        summary = JobSummary(
            job_id=job.id,
            total_inr_spend=str(total_inr),
            total_usd_spend=str(total_usd),
            top_merchants=", ".join(
                merchant for merchant, _ in top_merchants_list
            ),
            anomaly_count=len(anomalies),
            narrative=ai_summary.get(
                "narrative",
                "Unable to generate summary."
            ),
            risk_level=ai_summary.get(
                "risk_level",
                "Unknown"
            )
        )

        db.add(summary)
        
        # Single final commit for processing completion
        db.commit()
        print(f"Job {job_id} completed successfully.")

    except Exception as e:
        db.rollback()
        # Fresh fetch inside exception block to prevent stale object errors
        job = db.query(Job).filter(Job.id == job_id).first()
        if job:
            job.status = "failed"
            db.commit()
        print("Celery Error:", e)
        raise e  # Re-raise so Celery logs the failure explicitly
    finally:
        db.close()