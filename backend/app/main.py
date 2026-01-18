import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import schools, students, invoices, payments, account_statements, auth

app = FastAPI(
    title="Mattilda API",
    description="School billing management system",
    version="1.0.0"
)

# Configure CORS for development and production
allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

# Add production origins if environment variable is set
if cors_origins := os.getenv("CORS_ORIGINS"):
    allowed_origins.extend([origin.strip() for origin in cors_origins.split(",")])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(schools.router)
app.include_router(students.router)
app.include_router(invoices.router)
app.include_router(payments.router)
app.include_router(account_statements.router)


@app.get("/")
async def root():
    return {"message": "Mattilda API - School Billing Management System"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
