<div align="center">

# AI-Powered Transaction Processing Pipeline

An asynchronous backend for processing financial transaction CSV files using **FastAPI, PostgreSQL, Redis, Celery, Docker and Google Gemini**.

<p>

<img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
<img src="https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white"/>
<img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white"/>
<img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white"/>
<img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white"/>
<img src="https://img.shields.io/badge/Google%20Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white"/>

</p>

</div>

---

# Overview

This project is an AI-powered asynchronous transaction processing pipeline developed as part of the Backend & DevOps Engineering Assignment.

The application processes raw financial transaction CSV files by performing automated data cleaning, anomaly detection, AI-powered transaction categorization, and financial summary generation. Long-running tasks are executed asynchronously using Celery while Redis acts as the message broker and PostgreSQL stores all processed data.

The complete application is containerized using Docker Compose, allowing every service to start with a single command.

---

# Technical Review Video

A complete technical walkthrough explaining the architecture, request lifecycle, API demonstration, and scalability discussion is available below.

> 🎥 **Watch the Technical Walkthrough Video:**
> 
> [**Click here to watch the Architecture & API Demo**](https://drive.google.com/file/d/1gRdroL7ei9L9Nk11Z_bg3dhxcY7uLg_l/view?usp=sharing)
---

# Technology Stack

| Technology     | Purpose                     |
| -------------- | --------------------------- |
| FastAPI        | REST API Framework          |
| PostgreSQL     | Relational Database         |
| Redis          | Message Broker              |
| Celery         | Background Task Queue       |
| Docker         | Containerization            |
| Docker Compose | Service Orchestration       |
| SQLAlchemy     | ORM                         |
| Pandas         | Data Processing             |
| Google Gemini  | AI Classification & Summary |

---

# Project Structure

```text
alemeno-backend-assignment/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── tasks.py
│   ├── models.py
│   ├── database.py
│   └── celery_worker.py
│
├── images/
│   ├── architecture.png
│  
├── uploads/
│
├── transactions.csv
```

---

# System Architecture

<p align="center">
<img src="https://github.com/user-attachments/assets/5177cef8-8eb9-4b24-91ba-4eb6415493a8" width="700">
</p>

---

# Features

* Asynchronous CSV processing
* Background task execution using Celery
* PostgreSQL persistent storage
* Redis-based task queue
* Automatic data cleaning
* Duplicate removal
* Date normalization
* Currency normalization
* Statistical anomaly detection
* Currency anomaly detection
* AI-powered transaction categorization
* AI-generated financial summaries
* Dashboard analytics
* Merchant analytics
* Transaction filtering
* Job status polling
* Interactive Swagger documentation

---

# Setup

## Clone Repository

```bash
git clone https://github.com/Prer26/alemeno-backend-assignment.git

cd alemeno-backend-assignment
```

---

## Configure Environment

Create a `.env` file using `.env.example`.

```env
DATABASE_URL=postgresql://postgres:your_password@postgres:5432/alemeno_db

REDIS_URL=redis://redis:6379/0

GEMINI_API_KEY=your_gemini_api_key
```

---

## Start the Application

```bash
docker compose up --build
```

The following services start automatically:

* FastAPI
* PostgreSQL
* Redis
* Celery Worker

No additional setup is required.

---

# Running the API

Once all containers have started successfully, open your browser and navigate to:

### Swagger UI

```text
http://localhost:8000/docs
```

Swagger provides an interactive interface for:

* Uploading transaction CSV files
* Monitoring job status
* Viewing processed transaction results
* Accessing AI-generated summaries
* Viewing dashboard analytics
* Filtering transactions
* Testing every available API endpoint

Alternative OpenAPI documentation:

### ReDoc

```text
http://localhost:8000/redoc
```

---

# API Endpoints

| Method | Endpoint                 | Description                     |
| ------ | ------------------------ | ------------------------------- |
| POST   | `/jobs/upload`           | Upload transaction CSV          |
| GET    | `/jobs`                  | List all processing jobs        |
| GET    | `/jobs/{job_id}/status`  | Retrieve job status             |
| GET    | `/jobs/{job_id}/results` | Retrieve processed transactions |
| GET    | `/jobs/{job_id}/summary` | AI-generated financial summary  |
| GET    | `/transactions`          | Retrieve all transactions       |
| GET    | `/transactions/filter`   | Filter transactions             |
| GET    | `/dashboard`             | Dashboard statistics            |
| GET    | `/analytics/merchants`   | Merchant analytics              |

---

# Example cURL Requests

### Upload CSV

```bash
curl -X POST "http://localhost:8000/jobs/upload" \
-F "file=@transactions.csv"
```

### Get Job Status

```bash
curl http://localhost:8000/jobs/3/status
```

### Get Job Results

```bash
curl http://localhost:8000/jobs/3/results
```

### Get AI Summary

```bash
curl http://localhost:8000/jobs/3/summary
```

---

# Processing Pipeline

```text
CSV Upload
      │
      ▼
Create Job
      │
      ▼
Queue Background Task
      │
      ▼
Celery Worker
      │
      ▼
Data Cleaning
      │
      ▼
Anomaly Detection
      │
      ▼
Gemini Classification
      │
      ▼
AI Summary Generation
      │
      ▼
Store Results in PostgreSQL
      │
      ▼
Job Completed
```

---

# Application Screenshots

## Swagger Documentation

<p align="center">
<img width="1865" height="901" alt="image" src="https://github.com/user-attachments/assets/d2497331-13f5-4ef2-9053-d9b9234e98a5" />
</p>

---

## Job Status

<p align="center">
<img width="1770" height="502" alt="Screenshot 2026-06-28 094713" src="https://github.com/user-attachments/assets/ff5e16f8-0ae1-4df6-ac45-8cb5de2146aa" />
</p>

---

## Job Results

<p align="center">
<img width="1777" height="722" alt="Screenshot 2026-06-28 094734" src="https://github.com/user-attachments/assets/cf14ec8a-e8a4-4c65-919b-98e495cb7ef0" />
</p>

---

## AI Financial Summary

<p align="center">
<img width="1768" height="695" alt="Screenshot 2026-06-28 094756" src="https://github.com/user-attachments/assets/5e25fbc8-48ed-4426-946a-d2c2d69a4c3f" />
</p>

---

# Scalability Considerations

The current architecture is designed to support asynchronous processing and can be extended for higher workloads by:

* Deploying multiple FastAPI instances behind a load balancer
* Scaling Celery workers horizontally
* Using PostgreSQL indexing and connection pooling
* Introducing read replicas for database scalability
* Caching repeated merchant classifications to reduce LLM calls
* Moving uploaded files to object storage such as Amazon S3

---
# Design Decisions

- FastAPI was selected for building high-performance asynchronous REST APIs.
- Celery and Redis were used to offload long-running processing tasks from the API layer.
- PostgreSQL provides reliable relational storage for jobs and processed transactions.
- Google Gemini performs AI-powered transaction categorization and financial summarization.
- Docker Compose simplifies deployment by orchestrating all required services with a single command.
---
# Future Improvements

* Upgrade to the latest Google GenAI SDK
* JWT Authentication
* Alembic database migrations
* Unit and integration testing
* Pagination support
* Kubernetes deployment
* CI/CD pipeline
* Monitoring using Prometheus and Grafana

---

# Author

**Prerana Iyengar**

Backend & DevOps Engineering Assignment

---

<div align="center">

Built using FastAPI, PostgreSQL, Redis, Celery, Docker and Google Gemini AI.

</div>
