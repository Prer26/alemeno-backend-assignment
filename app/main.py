from fastapi import FastAPI, UploadFile
import os
import pandas as pd

app = FastAPI(
    title="AI Transaction Processing Pipeline"
)

jobs = []


def normalize_date(date_value):
    try:
        return pd.to_datetime(date_value).strftime("%Y-%m-%d")
    except:
        return None


def clean_transactions(df):

    # Fill missing category
    df["category"] = df["category"].fillna("Uncategorised")

    # Currency uppercase
    df["currency"] = df["currency"].astype(str).str.upper()

    # Status uppercase
    df["status"] = df["status"].astype(str).str.upper()

    # Remove $
    df["amount"] = (
        df["amount"]
        .astype(str)
        .str.replace("$", "", regex=False)
    )

    # Convert amount to float
    df["amount"] = pd.to_numeric(
        df["amount"],
        errors="coerce"
    )

    # Normalize dates
    df["date"] = df["date"].apply(normalize_date)

    # Remove duplicates
    df = df.drop_duplicates()

    return df


def detect_anomalies(df):

    anomalies = []

    for account in df["account_id"].unique():

        account_data = df[
            df["account_id"] == account
        ]

        median_amount = account_data["amount"].median()

        threshold = median_amount * 3

        anomaly_rows = account_data[
            account_data["amount"] > threshold
        ]

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

    domestic_brands = [
        "Swiggy",
        "Ola",
        "IRCTC"
    ]

    anomalies = []

    for _, row in df.iterrows():

        if (
            row["currency"] == "USD"
            and row["merchant"] in domestic_brands
        ):

            anomalies.append({
                "txn_id": row["txn_id"],
                "merchant": row["merchant"],
                "currency": row["currency"],
                "reason": "Domestic merchant using USD"
            })

    return anomalies


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

    print("\n===== CLEANED DATA =====")
    print(clean_df.head())

    print("\n===== DATA INFO =====")
    print(clean_df.info())

    print("\n===== AMOUNT ANOMALIES =====")
    print(anomalies)

    print("\n===== CURRENCY ANOMALIES =====")
    print(currency_anomalies)

    job_id = len(jobs) + 1

    job = {
        "job_id": job_id,
        "filename": file.filename,
        "status": "pending",
        "row_count_raw": len(raw_df),
        "row_count_clean": len(clean_df),
        "anomaly_count": len(anomalies),
        "currency_anomaly_count": len(currency_anomalies),
        "columns": list(clean_df.columns)
    }

    jobs.append(job)

    return job


@app.get("/jobs/{job_id}/status")
def get_job_status(job_id: int):

    for job in jobs:
        if job["job_id"] == job_id:
            return job

    return {"error": "Job not found"}


@app.get("/jobs")
def get_all_jobs():
    return jobs