from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    filename = Column(String, nullable=False)
    status = Column(String, nullable=False)

    row_count_raw = Column(Integer)
    row_count_clean = Column(Integer)

    anomaly_count = Column(Integer)
    currency_anomaly_count = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    job_id = Column(Integer)

    txn_id = Column(String)
    date = Column(String)
    merchant = Column(String)

    amount = Column(String)

    currency = Column(String)
    status = Column(String)

    category = Column(String)

    account_id = Column(String)

    notes = Column(String)

    is_anomaly = Column(String)
class JobSummary(Base):
    __tablename__ = "job_summaries"

    id = Column(Integer, primary_key=True, index=True)

    job_id = Column(Integer, unique=True)

    total_inr_spend = Column(String)

    total_usd_spend = Column(String)

    top_merchants = Column(String)

    anomaly_count = Column(Integer)

    narrative = Column(String)

    risk_level = Column(String)