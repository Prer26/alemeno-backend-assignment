import os
from dotenv import load_dotenv
import pandas as pd
import google.generativeai as genai
from fastapi import FastAPI, UploadFile, Query, HTTPException
from app.tasks import process_csv
import json
from app.database import engine, SessionLocal
from app.models import Base, Job, Transaction, JobSummary

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")
app = FastAPI(title="AI Transaction Processing Pipeline")

Base.metadata.create_all(bind=engine)


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
    for _, row in df.iterrows():
        if row["currency"] == "USD" and row["merchant"] in domestic:
            anomalies.append({
                "txn_id": row["txn_id"],
                "merchant": row["merchant"],
                "currency": row["currency"],
                "reason": "Domestic merchant using USD"
            })
    return anomalies


def classify_transaction(merchant, amount):
    prompt = f"""
    Classify this bank transaction.

    Merchant: {merchant}
    Amount: {amount}

    Return ONLY one category from:
    Food
    Shopping
    Travel
    Transport
    Utilities
    Cash Withdrawal
    Entertainment
    Other
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return "Other"


@app.get("/")
def root():
    return {"message": "Alemeno Backend Running"}


@app.post("/jobs/upload")
async def upload_csv(file: UploadFile):
    os.makedirs("uploads", exist_ok=True)
    filepath = f"uploads/{file.filename}"

    with open(filepath, "wb") as buffer:
        buffer.write(await file.read())

    raw_df = pd.read_csv(filepath)
    clean_df = clean_transactions(raw_df)
    anomalies = detect_anomalies(clean_df)
    currency_anomalies = detect_currency_anomalies(clean_df)

    db = SessionLocal()
    try:
        new_job = Job(
            filename=file.filename,
            status="pending",
            row_count_raw=len(raw_df),
            row_count_clean=len(clean_df),
            anomaly_count=len(anomalies),
            currency_anomaly_count=len(currency_anomalies)
        )
        db.add(new_job)
        db.commit()
        db.refresh(new_job)
        
        # Trigger Celery background task
        process_csv.delay(filepath, new_job.id)
        
        # Cleaned up response mapping
        return {
            "job_id": new_job.id,
            "filename": new_job.filename,
            "status": "pending",
            "message": "Job submitted successfully for processing",
            "row_count_raw": len(raw_df),
            "row_count_clean": len(clean_df),
            "anomaly_count": len(anomalies),
            "currency_anomaly_count": len(currency_anomalies),
            "columns": list(clean_df.columns)
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()


@app.get("/jobs/{job_id}/status")
def get_job_status(job_id: int):

    db = SessionLocal()

    try:

        job = db.query(Job).filter(Job.id == job_id).first()

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )

        return {
            "job_id": job.id,
            "filename": job.filename,
            "status": job.status,
            "row_count_raw": job.row_count_raw,
            "row_count_clean": job.row_count_clean,
            "anomaly_count": job.anomaly_count,
            "currency_anomaly_count": job.currency_anomaly_count,
            "created_at": job.created_at
        }

    finally:

        db.close()


@app.get("/jobs")
def get_all_jobs(status: str = Query(None)):
    db = SessionLocal()
    query = db.query(Job)
    if status:
        query = query.filter(Job.status == status)
    jobs = query.all()
    db.close()

    return [
        {
            "job_id": j.id,
            "filename": j.filename,
            "status": j.status,
            "row_count_raw": j.row_count_raw,
            "row_count_clean": j.row_count_clean,
            "anomaly_count": j.anomaly_count,
            "currency_anomaly_count": j.currency_anomaly_count,
            "created_at": j.created_at
        }
        for j in jobs
    ]


@app.get("/transactions")
def get_transactions():
    db = SessionLocal()
    transactions = db.query(Transaction).all()
    db.close()

    return [
        {
            "id": t.id,
            "job_id": t.job_id,
            "txn_id": t.txn_id,
            "date": t.date,
            "merchant": t.merchant,
            "amount": t.amount,
            "currency": t.currency,
            "status": t.status,
            "category": t.category,
            "account_id": t.account_id,
            "notes": t.notes,
            "is_anomaly": t.is_anomaly
        }
        for t in transactions
    ]


@app.get("/dashboard")
def dashboard():
    db = SessionLocal()
    total_jobs = db.query(Job).count()
    total_transactions = db.query(Transaction).count()
    total_anomalies = db.query(Transaction).filter(Transaction.is_anomaly == "Yes").count()
    success = db.query(Transaction).filter(Transaction.status == "SUCCESS").count()
    failed = db.query(Transaction).filter(Transaction.status == "FAILED").count()
    pending = db.query(Transaction).filter(Transaction.status == "PENDING").count()
    db.close()

    return {
        "total_jobs": total_jobs,
        "total_transactions": total_transactions,
        "total_anomalies": total_anomalies,
        "success_transactions": success,
        "failed_transactions": failed,
        "pending_transactions": pending
    }


@app.get("/jobs/{job_id}/results")
def get_job_results(job_id: int):

    db = SessionLocal()

    try:

        job = db.query(Job).filter(Job.id == job_id).first()

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )

        transactions = db.query(Transaction).filter(
            Transaction.job_id == job_id
        ).all()

        summary = db.query(JobSummary).filter(
            JobSummary.job_id == job_id
        ).first()

        category_spend = {}

        anomalies = []

        for t in transactions:

            amount = float(t.amount)

            category_spend[t.category] = (
                category_spend.get(t.category, 0) + amount
            )

            if t.is_anomaly == "Yes":

                anomalies.append({
                    "txn_id": t.txn_id,
                    "merchant": t.merchant,
                    "amount": amount,
                    "currency": t.currency
                })

        return {

            "job": {
                "id": job.id,
                "filename": job.filename,
                "status": job.status
            },

            "summary": None if summary is None else {

                "total_inr_spend": summary.total_inr_spend,

                "total_usd_spend": summary.total_usd_spend,

                "top_merchants": summary.top_merchants,

                "anomaly_count": summary.anomaly_count,

                "narrative": summary.narrative,

                "risk_level": summary.risk_level

            },

            "category_spend": category_spend,

            "anomalies": anomalies,

            "transactions": [

                {

                    "txn_id": t.txn_id,

                    "date": t.date,

                    "merchant": t.merchant,

                    "amount": t.amount,

                    "currency": t.currency,

                    "status": t.status,

                    "category": t.category,

                    "account_id": t.account_id,

                    "notes": t.notes,

                    "is_anomaly": t.is_anomaly

                }

                for t in transactions

            ]

        }

    finally:

        db.close()


@app.get("/jobs/{job_id}/summary")
def get_ai_summary(job_id: int):

    db = SessionLocal()

    transactions = db.query(Transaction).filter(
        Transaction.job_id == job_id
    ).all()

    db.close()

    if not transactions:
        return {"message": "No transactions found"}

    text = ""

    for t in transactions:

        text += (
            f"Merchant: {t.merchant}, "
            f"Amount: {t.amount}, "
            f"Currency: {t.currency}, "
            f"Status: {t.status}, "
            f"Category: {t.category}, "
            f"Anomaly: {t.is_anomaly}\n"
        )

    prompt = f"""
    Analyze the following financial transactions.

    {text}

    Return ONLY valid JSON in this format:

    {{
        "total_spend_by_currency": {{
        "INR": 0,
        "USD": 0
    }},
    "top_merchants": [
    "...",
    "...",
    "..."
  ],
  "anomaly_count": 0,
  "narrative": "2-3 sentence summary",
  "risk_level": "Low"
}}

Do not return markdown.
Do not return explanation.
Only JSON.
"""

    try:

        response = model.generate_content(prompt)

        try:

            summary = json.loads(response.text)

            return {
                "job_id": job_id,
                "summary": summary
            }

        except Exception:

            return {
                "job_id": job_id,
                "raw_summary": response.text
            }

    except Exception as e:

        return {
            "job_id": job_id,
            "summary": "Gemini quota exceeded or error occurred.",
            "error": str(e)
        }

@app.get("/transactions/filter")
def filter_transactions(status: str = None, category: str = None):
    db = SessionLocal()
    query = db.query(Transaction)

    if status:
        query = query.filter(Transaction.status == status)
    if category:
        query = query.filter(Transaction.category == category)

    transactions = query.all()
    db.close()
    return transactions


@app.get("/analytics/merchants")
def merchant_analytics():
    db = SessionLocal()
    transactions = db.query(Transaction).all()
    db.close()

    analytics = {}
    for t in transactions:
        merchant = t.merchant
        try:
            amount = float(t.amount)
        except ValueError:
            amount = 0.0

        if merchant not in analytics:
            analytics[merchant] = {
                "transactions": 0,
                "total_amount": 0.0
            }

        analytics[merchant]["transactions"] += 1
        analytics[merchant]["total_amount"] += amount

    return analytics