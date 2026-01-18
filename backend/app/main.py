from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import schools, students, invoices, payments, account_statements, auth

app = FastAPI(
    title="Mattilda API",
    description="School billing management system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
