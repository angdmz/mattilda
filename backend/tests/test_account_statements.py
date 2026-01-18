import pytest
from http import HTTPStatus
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestAccountStatements:
    async def test_student_account_statement(self, authenticated_client: AsyncClient):
        school_response = await authenticated_client.post("/schools/", json={"name": "Test School"})
        school_id = school_response.json()["id"]

        student_response = await authenticated_client.post(
            "/students/",
            json={"name": "John Doe", "school_id": school_id}
        )
        student_id = student_response.json()["id"]

        await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student_id,
                "amount_cents": 10000,
                "currency": "USD",
                "description": "Tuition"
            }
        )

        await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student_id,
                "amount_cents": 5000,
                "currency": "USD",
                "description": "Books"
            }
        )

        response = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert data["student_id"] == student_id
        assert data["total_invoiced"]["amount_cents"] == 15000
        assert data["total_paid"]["amount_cents"] == 0
        assert data["total_outstanding"]["amount_cents"] == 15000
        assert len(data["invoices"]) == 2

    async def test_school_account_statement(self, authenticated_client: AsyncClient):
        school_response = await authenticated_client.post("/schools/", json={"name": "Test School"})
        school_id = school_response.json()["id"]

        student1_response = await authenticated_client.post(
            "/students/",
            json={"name": "John Doe", "school_id": school_id}
        )
        student1_id = student1_response.json()["id"]

        student2_response = await authenticated_client.post(
            "/students/",
            json={"name": "Jane Smith", "school_id": school_id}
        )
        student2_id = student2_response.json()["id"]

        await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student1_id,
                "amount_cents": 10000,
                "currency": "USD"
            }
        )

        await authenticated_client.post(
            "/invoices/",
            json={
                "student_id": student2_id,
                "amount_cents": 8000,
                "currency": "USD"
            }
        )

        response = await authenticated_client.get(f"/account-statements/schools/{school_id}")
        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert data["school_id"] == school_id
        assert data["total_invoiced"]["amount_cents"] == 18000
        assert data["total_paid"]["amount_cents"] == 0
        assert data["total_outstanding"]["amount_cents"] == 18000
        assert data["number_of_students"] == 2
        assert len(data["students"]) == 2

    async def test_school_statement_with_payments(self, authenticated_client: AsyncClient):
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

        await authenticated_client.post(
            "/payments/",
            json={
                "student_id": student_id,
                "amount_cents": 6000,
                "currency": "USD",
                "payment_method": "cash",
                "imputations": [
                    {"invoice_id": invoice_id, "amount_cents": 6000}
                ]
            }
        )

        response = await authenticated_client.get(f"/account-statements/schools/{school_id}")
        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert data["total_invoiced"]["amount_cents"] == 10000
        assert data["total_paid"]["amount_cents"] == 6000
        assert data["total_outstanding"]["amount_cents"] == 4000

    async def test_freshly_created_school_statement(self, authenticated_client: AsyncClient):
        """Test that getting a statement for a school with no students doesn't cause a 500 error."""
        school_response = await authenticated_client.post("/schools/", json={"name": "Empty School"})
        school_id = school_response.json()["id"]

        response = await authenticated_client.get(f"/account-statements/schools/{school_id}")
        assert response.status_code == HTTPStatus.OK

        data = response.json()
        assert data["school_id"] == school_id
        assert data["total_invoiced"]["amount_cents"] == 0
        assert data["total_paid"]["amount_cents"] == 0
        assert data["total_outstanding"]["amount_cents"] == 0
        assert data["number_of_students"] == 0
        assert len(data["students"]) == 0
