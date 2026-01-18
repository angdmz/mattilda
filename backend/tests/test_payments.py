import pytest
from http import HTTPStatus
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestPayments:
    async def test_create_payment_with_full_invoice_payment(self, authenticated_client: AsyncClient):
        school_response = await authenticated_client.post("/schools/", json={"name": "Test School"})
        school_id = school_response.json()["id"]

        student_response = await authenticated_client.post(
            "/students/",
            json={"name": "John Doe", "school_id": school_id}
        )
        student_id = student_response.json()["id"]

        invoice_response = await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student_id,
                "amount_cents": 10000,
                "currency": "USD",
                "description": "Tuition"
            }
        )
        invoice_id = invoice_response.json()["id"]

        payment_response = await authenticated_client.post(
            "/payments/",
            json={
                "student_id": student_id,
                "amount_cents": 10000,
                "currency": "USD",
                "payment_method": "credit_card",
                "imputations": [
                    {"invoice_id": invoice_id, "amount_cents": 10000}
                ]
            }
        )
        assert payment_response.status_code == HTTPStatus.CREATED
        data = payment_response.json()
        assert data["amount_cents"] == 10000
        assert data["student_id"] == student_id

    async def test_flow_full_payment_imputed_to_invoice_completely(self, authenticated_client: AsyncClient):
        school_response = await authenticated_client.post("/schools/", json={"name": "Flow School"})
        assert school_response.status_code == HTTPStatus.CREATED
        school_id = school_response.json()["id"]

        student_response = await authenticated_client.post(
            "/students/",
            json={"name": "Flow Student", "school_id": school_id},
        )
        assert student_response.status_code == HTTPStatus.CREATED
        student_id = student_response.json()["id"]

        invoice_response = await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student_id,
                "amount_cents": 25000,
                "currency": "USD",
                "description": "Flow Invoice",
            },
        )
        assert invoice_response.status_code == HTTPStatus.CREATED
        invoice_id = invoice_response.json()["id"]

        payment_response = await authenticated_client.post(
            "/payments/",
            json={
                "student_id": student_id,
                "amount_cents": 25000,
                "currency": "USD",
                "payment_method": "bank_transfer",
                "imputations": [
                    {"invoice_id": invoice_id, "amount_cents": 25000},
                ],
            },
        )
        assert payment_response.status_code == HTTPStatus.CREATED

        statement_response = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert statement_response.status_code == HTTPStatus.OK
        statement = statement_response.json()

        assert statement["total_invoiced"]["amount_cents"] == 25000
        assert statement["total_paid"]["amount_cents"] == 25000
        assert statement["total_outstanding"]["amount_cents"] == 0
        assert len(statement["invoices"]) == 1

        inv = statement["invoices"][0]
        assert str(inv["id"]) == str(invoice_id)
        assert inv["amount"]["amount_cents"] == 25000
        assert inv["paid_amount"]["amount_cents"] == 25000
        assert inv["outstanding_amount"]["amount_cents"] == 0

    async def test_create_payment_with_partial_payment(self, authenticated_client: AsyncClient):
        school_response = await authenticated_client.post("/schools/", json={"name": "Test School"})
        school_id = school_response.json()["id"]

        student_response = await authenticated_client.post(
            "/students/",
            json={"name": "John Doe", "school_id": school_id}
        )
        student_id = student_response.json()["id"]

        invoice_response = await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student_id,
                "amount_cents": 10000,
                "currency": "USD",
                "description": "Tuition"
            }
        )
        invoice_id = invoice_response.json()["id"]

        payment_response = await authenticated_client.post(
            "/payments/",
            json={
                "student_id": student_id,
                "amount_cents": 5000,
                "currency": "USD",
                "payment_method": "credit_card",
                "imputations": [
                    {"invoice_id": invoice_id, "amount_cents": 5000}
                ]
            }
        )
        assert payment_response.status_code == HTTPStatus.CREATED

        statement_response = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert statement_response.status_code == HTTPStatus.OK
        statement = statement_response.json()
        assert statement["total_outstanding"]["amount_cents"] == 5000

    async def test_create_payment_split_across_invoices(self, authenticated_client: AsyncClient):
        school_response = await authenticated_client.post("/schools/", json={"name": "Test School"})
        school_id = school_response.json()["id"]

        student_response = await authenticated_client.post(
            "/students/",
            json={"name": "John Doe", "school_id": school_id}
        )
        student_id = student_response.json()["id"]

        invoice1_response = await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student_id,
                "amount_cents": 10000,
                "currency": "USD",
                "description": "Tuition"
            }
        )
        invoice1_id = invoice1_response.json()["id"]

        invoice2_response = await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student_id,
                "amount_cents": 5000,
                "currency": "USD",
                "description": "Books"
            }
        )
        invoice2_id = invoice2_response.json()["id"]

        payment_response = await authenticated_client.post(
            "/payments/",
            json={
                "student_id": student_id,
                "amount_cents": 12000,
                "currency": "USD",
                "payment_method": "credit_card",
                "imputations": [
                    {"invoice_id": invoice1_id, "amount_cents": 10000},
                    {"invoice_id": invoice2_id, "amount_cents": 2000}
                ]
            }
        )
        assert payment_response.status_code == HTTPStatus.CREATED

        statement_response = await authenticated_client.get(f"/account-statements/students/{student_id}")
        statement = statement_response.json()
        assert statement["total_outstanding"]["amount_cents"] == 3000

    async def test_payment_validation_amount_mismatch(self, authenticated_client: AsyncClient):
        school_response = await authenticated_client.post("/schools/", json={"name": "Test School"})
        school_id = school_response.json()["id"]

        student_response = await authenticated_client.post(
            "/students/",
            json={"name": "John Doe", "school_id": school_id}
        )
        student_id = student_response.json()["id"]

        invoice_response = await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student_id,
                "amount_cents": 10000,
                "currency": "USD"
            }
        )
        invoice_id = invoice_response.json()["id"]

        payment_response = await authenticated_client.post(
            "/payments/",
            json={
                "student_id": student_id,
                "amount_cents": 10000,
                "currency": "USD",
                "payment_method": "cash",
                "imputations": [
                    {"invoice_id": invoice_id, "amount_cents": 5000}
                ]
            }
        )
        assert payment_response.status_code == HTTPStatus.BAD_REQUEST

    async def test_payment_below_invoice_incomplete_payment(self, authenticated_client: AsyncClient):
        """Test a payment that is less than the invoice amount (incomplete payment)."""
        school_response = await authenticated_client.post("/schools/", json={"name": "Test School"})
        school_id = school_response.json()["id"]

        student_response = await authenticated_client.post(
            "/students/",
            json={"name": "Jane Doe", "school_id": school_id}
        )
        student_id = student_response.json()["id"]

        invoice_response = await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student_id,
                "amount_cents": 15000,
                "currency": "USD",
                "description": "Monthly Tuition"
            }
        )
        invoice_id = invoice_response.json()["id"]

        payment_response = await authenticated_client.post(
            "/payments/",
            json={
                "student_id": student_id,
                "amount_cents": 8000,
                "currency": "USD",
                "payment_method": "cash",
                "imputations": [
                    {"invoice_id": invoice_id, "amount_cents": 8000}
                ]
            }
        )
        assert payment_response.status_code == HTTPStatus.CREATED

        statement_response = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert statement_response.status_code == HTTPStatus.OK
        statement = statement_response.json()

        assert statement["total_invoiced"]["amount_cents"] == 15000
        assert statement["total_paid"]["amount_cents"] == 8000
        assert statement["total_outstanding"]["amount_cents"] == 7000

        inv = statement["invoices"][0]
        assert inv["amount"]["amount_cents"] == 15000
        assert inv["paid_amount"]["amount_cents"] == 8000
        assert inv["outstanding_amount"]["amount_cents"] == 7000

    async def test_payment_covering_two_full_invoices(self, authenticated_client: AsyncClient):
        """Test a payment that fully covers two invoices."""
        school_response = await authenticated_client.post("/schools/", json={"name": "Test School"})
        school_id = school_response.json()["id"]

        student_response = await authenticated_client.post(
            "/students/",
            json={"name": "Bob Smith", "school_id": school_id}
        )
        student_id = student_response.json()["id"]

        invoice1_response = await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student_id,
                "amount_cents": 12000,
                "currency": "USD",
                "description": "September Tuition"
            }
        )
        invoice1_id = invoice1_response.json()["id"]

        invoice2_response = await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student_id,
                "amount_cents": 8000,
                "currency": "USD",
                "description": "October Tuition"
            }
        )
        invoice2_id = invoice2_response.json()["id"]

        payment_response = await authenticated_client.post(
            "/payments/",
            json={
                "student_id": student_id,
                "amount_cents": 20000,
                "currency": "USD",
                "payment_method": "bank_transfer",
                "imputations": [
                    {"invoice_id": invoice1_id, "amount_cents": 12000},
                    {"invoice_id": invoice2_id, "amount_cents": 8000}
                ]
            }
        )
        assert payment_response.status_code == HTTPStatus.CREATED

        statement_response = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert statement_response.status_code == HTTPStatus.OK
        statement = statement_response.json()

        assert statement["total_invoiced"]["amount_cents"] == 20000
        assert statement["total_paid"]["amount_cents"] == 20000
        assert statement["total_outstanding"]["amount_cents"] == 0

        for inv in statement["invoices"]:
            assert inv["outstanding_amount"]["amount_cents"] == 0

    async def test_two_payments_covering_single_invoice(self, authenticated_client: AsyncClient):
        """Test two separate payments that together fully cover a single invoice."""
        school_response = await authenticated_client.post("/schools/", json={"name": "Test School"})
        school_id = school_response.json()["id"]

        student_response = await authenticated_client.post(
            "/students/",
            json={"name": "Alice Johnson", "school_id": school_id}
        )
        student_id = student_response.json()["id"]

        invoice_response = await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student_id,
                "amount_cents": 20000,
                "currency": "USD",
                "description": "Annual Fee"
            }
        )
        invoice_id = invoice_response.json()["id"]

        payment1_response = await authenticated_client.post(
            "/payments/",
            json={
                "student_id": student_id,
                "amount_cents": 12000,
                "currency": "USD",
                "payment_method": "credit_card",
                "imputations": [
                    {"invoice_id": invoice_id, "amount_cents": 12000}
                ]
            }
        )
        assert payment1_response.status_code == HTTPStatus.CREATED

        payment2_response = await authenticated_client.post(
            "/payments/",
            json={
                "student_id": student_id,
                "amount_cents": 8000,
                "currency": "USD",
                "payment_method": "cash",
                "imputations": [
                    {"invoice_id": invoice_id, "amount_cents": 8000}
                ]
            }
        )
        assert payment2_response.status_code == HTTPStatus.CREATED

        statement_response = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert statement_response.status_code == HTTPStatus.OK
        statement = statement_response.json()

        assert statement["total_invoiced"]["amount_cents"] == 20000
        assert statement["total_paid"]["amount_cents"] == 20000
        assert statement["total_outstanding"]["amount_cents"] == 0

        inv = statement["invoices"][0]
        assert inv["amount"]["amount_cents"] == 20000
        assert inv["paid_amount"]["amount_cents"] == 20000
        assert inv["outstanding_amount"]["amount_cents"] == 0

    async def test_payment_covering_full_invoice_and_partial_second(self, authenticated_client: AsyncClient):
        """Test a payment that fully covers one invoice and partially covers another."""
        school_response = await authenticated_client.post("/schools/", json={"name": "Test School"})
        school_id = school_response.json()["id"]

        student_response = await authenticated_client.post(
            "/students/",
            json={"name": "Charlie Brown", "school_id": school_id}
        )
        student_id = student_response.json()["id"]

        invoice1_response = await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student_id,
                "amount_cents": 10000,
                "currency": "USD",
                "description": "Course Fee"
            }
        )
        invoice1_id = invoice1_response.json()["id"]

        invoice2_response = await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student_id,
                "amount_cents": 15000,
                "currency": "USD",
                "description": "Lab Fee"
            }
        )
        invoice2_id = invoice2_response.json()["id"]

        payment_response = await authenticated_client.post(
            "/payments/",
            json={
                "student_id": student_id,
                "amount_cents": 18000,
                "currency": "USD",
                "payment_method": "debit_card",
                "imputations": [
                    {"invoice_id": invoice1_id, "amount_cents": 10000},
                    {"invoice_id": invoice2_id, "amount_cents": 8000}
                ]
            }
        )
        assert payment_response.status_code == HTTPStatus.CREATED

        statement_response = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert statement_response.status_code == HTTPStatus.OK
        statement = statement_response.json()

        assert statement["total_invoiced"]["amount_cents"] == 25000
        assert statement["total_paid"]["amount_cents"] == 18000
        assert statement["total_outstanding"]["amount_cents"] == 7000

        invoices_by_id = {inv["id"]: inv for inv in statement["invoices"]}
        
        inv1 = invoices_by_id[invoice1_id]
        assert inv1["amount"]["amount_cents"] == 10000
        assert inv1["paid_amount"]["amount_cents"] == 10000
        assert inv1["outstanding_amount"]["amount_cents"] == 0

        inv2 = invoices_by_id[invoice2_id]
        assert inv2["amount"]["amount_cents"] == 15000
        assert inv2["paid_amount"]["amount_cents"] == 8000
        assert inv2["outstanding_amount"]["amount_cents"] == 7000

    async def test_payment_covering_two_partial_invoices(self, authenticated_client: AsyncClient):
        """Test a payment that partially covers two different invoices."""
        school_response = await authenticated_client.post("/schools/", json={"name": "Test School"})
        school_id = school_response.json()["id"]

        student_response = await authenticated_client.post(
            "/students/",
            json={"name": "Diana Prince", "school_id": school_id}
        )
        student_id = student_response.json()["id"]

        invoice1_response = await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student_id,
                "amount_cents": 20000,
                "currency": "USD",
                "description": "Semester 1"
            }
        )
        invoice1_id = invoice1_response.json()["id"]

        invoice2_response = await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student_id,
                "amount_cents": 18000,
                "currency": "USD",
                "description": "Semester 2"
            }
        )
        invoice2_id = invoice2_response.json()["id"]

        payment_response = await authenticated_client.post(
            "/payments/",
            json={
                "student_id": student_id,
                "amount_cents": 15000,
                "currency": "USD",
                "payment_method": "wire_transfer",
                "imputations": [
                    {"invoice_id": invoice1_id, "amount_cents": 9000},
                    {"invoice_id": invoice2_id, "amount_cents": 6000}
                ]
            }
        )
        assert payment_response.status_code == HTTPStatus.CREATED

        statement_response = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert statement_response.status_code == HTTPStatus.OK
        statement = statement_response.json()

        assert statement["total_invoiced"]["amount_cents"] == 38000
        assert statement["total_paid"]["amount_cents"] == 15000
        assert statement["total_outstanding"]["amount_cents"] == 23000

        invoices_by_id = {inv["id"]: inv for inv in statement["invoices"]}
        
        inv1 = invoices_by_id[invoice1_id]
        assert inv1["amount"]["amount_cents"] == 20000
        assert inv1["paid_amount"]["amount_cents"] == 9000
        assert inv1["outstanding_amount"]["amount_cents"] == 11000

        inv2 = invoices_by_id[invoice2_id]
        assert inv2["amount"]["amount_cents"] == 18000
        assert inv2["paid_amount"]["amount_cents"] == 6000
        assert inv2["outstanding_amount"]["amount_cents"] == 12000
