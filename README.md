# AI-Powered Transaction Processing Pipeline

## Overview

This project is an AI-powered backend system that processes raw financial transaction CSV files asynchronously. It cleans inconsistent data, detects anomalies, classifies uncategorized transactions using Google's Gemini LLM, and generates an AI-powered financial summary.

The entire application is containerized using Docker and consists of FastAPI, PostgreSQL, Redis, and Celery.

---

## Features

* CSV file upload
* Asynchronous background processing using Celery
* PostgreSQL database for persistent storage
* Redis as message broker
* Dockerized microservice architecture
* Automatic data cleaning
* Duplicate removal
* Date normalization
* Currency normalization
* Statistical anomaly detection
* Currency anomaly detection
* AI-powered transaction categorization using Gemini
* Batch LLM processing
* Retry mechanism with exponential backoff
* AI-generated spending summary
* Dashboard API
* Merchant analytics
* Transaction filtering
* Job status polling

---

## Tech Stack

* FastAPI
* PostgreSQL
* Celery
* Redis
* Docker
* Docker Compose
* SQLAlchemy
* Pandas
* Google Gemini API

---

## Project Structure

```text
alemeno-backend-assignment/
│
├── app/
│   ├── main.py
│   ├── tasks.py
│   ├── models.py
│   ├── database.py
│   ├── celery_worker.py
│
├── uploads/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## System Architecture

```text
                Client
                   │
                   ▼
            FastAPI Backend
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
     PostgreSQL           Redis
                               │
                               ▼
                        Celery Worker
                               │
         ┌─────────────────────┴─────────────────────┐
         ▼                                           ▼
   Data Cleaning                           Gemini AI
         │                                           │
         └─────────────────────┬─────────────────────┘
                               ▼
                        Job Summary Storage
```

---

## Setup

### Clone Repository

```bash
git clone https://github.com/Prer26/alemeno-backend-assignment.git

cd alemeno-backend-assignment
```

---

### Configure Environment

Create a `.env` file using `.env.example`.

Example:

```env
DATABASE_URL=postgresql://postgres:your_password@postgres:5432/alemeno_db

REDIS_URL=redis://redis:6379/0

GEMINI_API_KEY=your_api_key
```

---

### Start Application

```bash
docker compose up --build
```

The application will automatically start:

* FastAPI
* PostgreSQL
* Redis
* Celery Worker

No manual setup is required.

---

## API Endpoints

### Upload CSV

```
POST /jobs/upload
```

Uploads a transaction CSV and immediately returns a Job ID.

---

### Job Status

```
GET /jobs/{job_id}/status
```

Returns the current processing status.

---

### Job Results

```
GET /jobs/{job_id}/results
```

Returns:

* Processed transactions
* Anomaly list
* Category-wise spending
* AI-generated summary

---

### AI Summary

```
GET /jobs/{job_id}/summary
```

Returns a structured financial summary generated using Gemini.

---

### List Jobs

```
GET /jobs
```

Lists all uploaded jobs.

Supports:

```
GET /jobs?status=completed
```

---

### Dashboard

```
GET /dashboard
```

Returns overall system statistics.

---

### Merchant Analytics

```
GET /analytics/merchants
```

Returns merchant-wise spending analytics.

---

### Filter Transactions

```
GET /transactions/filter
```

Supports filtering by:

* Status
* Category
* Currency

---

## Processing Pipeline

1. Upload CSV
2. Create Job
3. Queue Background Task
4. Clean Data
5. Detect Anomalies
6. Batch Gemini Classification
7. Generate AI Summary
8. Store Results
9. Mark Job Complete

---

## Future Improvements

* Migrate to the latest Google GenAI SDK
* Add JWT Authentication
* Database migrations using Alembic
* Pagination for transaction APIs
* Unit and integration tests
* Kubernetes deployment

---

## Author

**Prerana Iyengar**

Backend & AI Engineering Assignment
