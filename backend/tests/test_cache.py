import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from httpx import AsyncClient
from http import HTTPStatus
from tests.test_schemas import (
    create_school_data,
    create_student_data,
    create_invoice_data,
    create_payment_data,
    PaymentMethod,
)


pytestmark = pytest.mark.asyncio


class TestAccountStatementCaching:
    """Test caching behavior for account statements."""
    
    async def test_student_statement_cache_miss_then_hit(self, authenticated_client: AsyncClient):
        """Test that first request caches, second request uses cache."""
        # Create test data
        school_response = await authenticated_client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        student_response = await authenticated_client.post(
            "/students/",
            json=create_student_data("John Doe", school_id)
        )
        student_id = student_response.json()["id"]
        
        await authenticated_client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 10000, currency="USD", description="Tuition")
        )
        
        # First request - should be cache miss
        response1 = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert response1.status_code == HTTPStatus.OK
        data1 = response1.json()
        
        # Second request - should be cache hit (same data)
        response2 = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert response2.status_code == HTTPStatus.OK
        data2 = response2.json()
        
        # Data should be identical
        assert data1 == data2
        assert data1["total_invoiced"]["amount_cents"] == 10000
    
    async def test_school_statement_cache_miss_then_hit(self, authenticated_client: AsyncClient):
        """Test that school statement caching works."""
        # Create test data
        school_response = await authenticated_client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        student_response = await authenticated_client.post(
            "/students/",
            json=create_student_data("Jane Doe", school_id)
        )
        student_id = student_response.json()["id"]
        
        await authenticated_client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 5000, currency="USD", description="Books")
        )
        
        # First request - cache miss
        response1 = await authenticated_client.get(f"/account-statements/schools/{school_id}")
        assert response1.status_code == HTTPStatus.OK
        data1 = response1.json()
        
        # Second request - cache hit
        response2 = await authenticated_client.get(f"/account-statements/schools/{school_id}")
        assert response2.status_code == HTTPStatus.OK
        data2 = response2.json()
        
        # Data should be identical
        assert data1 == data2
        assert data1["total_invoiced"]["amount_cents"] == 5000
        assert data1["number_of_students"] == 1


class TestCacheInvalidationOnInvoiceChanges:
    """Test that cache is invalidated when invoices are created/updated/deleted."""
    
    async def test_cache_invalidated_on_invoice_creation(self, authenticated_client: AsyncClient):
        """Test cache invalidation when creating a new invoice."""
        # Setup
        school_response = await authenticated_client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        student_response = await authenticated_client.post(
            "/students/",
            json=create_student_data("Alice", school_id)
        )
        student_id = student_response.json()["id"]
        
        # Create first invoice
        await authenticated_client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 10000, currency="USD", description="First invoice")
        )
        
        # Get statement to populate cache
        response1 = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert response1.status_code == HTTPStatus.OK
        assert response1.json()["total_invoiced"]["amount_cents"] == 10000
        
        # Create second invoice - should invalidate cache
        await authenticated_client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 5000, currency="USD", description="Second invoice")
        )
        
        # Get statement again - should reflect new invoice
        response2 = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert response2.status_code == HTTPStatus.OK
        assert response2.json()["total_invoiced"]["amount_cents"] == 15000
    
    async def test_cache_invalidated_on_invoice_update(self, authenticated_client: AsyncClient):
        """Test cache invalidation when updating an invoice."""
        # Setup
        school_response = await authenticated_client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        student_response = await authenticated_client.post(
            "/students/",
            json=create_student_data("Bob", school_id)
        )
        student_id = student_response.json()["id"]
        
        # Create invoice
        invoice_response = await authenticated_client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 10000, currency="USD", description="Original")
        )
        invoice_id = invoice_response.json()["id"]
        
        # Get statement to populate cache
        response1 = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert response1.status_code == HTTPStatus.OK
        assert response1.json()["total_invoiced"]["amount_cents"] == 10000
        
        # Update invoice - should invalidate cache
        await authenticated_client.put(
            f"/invoices/{invoice_id}",
            json={"amount_cents": 20000}
        )
        
        # Get statement again - should reflect updated amount
        response2 = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert response2.status_code == HTTPStatus.OK
        assert response2.json()["total_invoiced"]["amount_cents"] == 20000
    
    async def test_cache_invalidated_on_invoice_deletion(self, authenticated_client: AsyncClient):
        """Test cache invalidation when deleting an invoice."""
        # Setup
        school_response = await authenticated_client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        student_response = await authenticated_client.post(
            "/students/",
            json=create_student_data("Charlie", school_id)
        )
        student_id = student_response.json()["id"]
        
        # Create invoice
        invoice_response = await authenticated_client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 10000, currency="USD", description="To be deleted")
        )
        invoice_id = invoice_response.json()["id"]
        
        # Get statement to populate cache
        response1 = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert response1.status_code == HTTPStatus.OK
        assert response1.json()["total_invoiced"]["amount_cents"] == 10000
        
        # Delete invoice - should invalidate cache
        await authenticated_client.delete(f"/invoices/{invoice_id}")
        
        # Get statement again - should show zero
        response2 = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert response2.status_code == HTTPStatus.OK
        assert response2.json()["total_invoiced"]["amount_cents"] == 0
    
    async def test_school_cache_invalidated_on_student_invoice_change(self, authenticated_client: AsyncClient):
        """Test that school cache is invalidated when student's invoice changes."""
        # Setup
        school_response = await authenticated_client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        student_response = await authenticated_client.post(
            "/students/",
            json=create_student_data("Diana", school_id)
        )
        student_id = student_response.json()["id"]
        
        # Create invoice
        await authenticated_client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 10000, currency="USD", description="First")
        )
        
        # Get school statement to populate cache
        response1 = await authenticated_client.get(f"/account-statements/schools/{school_id}")
        assert response1.status_code == HTTPStatus.OK
        assert response1.json()["total_invoiced"]["amount_cents"] == 10000
        
        # Create another invoice - should invalidate school cache
        await authenticated_client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 5000, currency="USD", description="Second")
        )
        
        # Get school statement again - should reflect new total
        response2 = await authenticated_client.get(f"/account-statements/schools/{school_id}")
        assert response2.status_code == HTTPStatus.OK
        assert response2.json()["total_invoiced"]["amount_cents"] == 15000


class TestCacheInvalidationOnPaymentChanges:
    """Test that cache is invalidated when payments are created/deleted."""
    
    async def test_cache_invalidated_on_payment_creation(self, authenticated_client: AsyncClient):
        """Test cache invalidation when creating a payment."""
        # Setup
        school_response = await authenticated_client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        student_response = await authenticated_client.post(
            "/students/",
            json=create_student_data("Eve", school_id)
        )
        student_id = student_response.json()["id"]
        
        # Create invoice
        invoice_response = await authenticated_client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 10000, currency="USD", description="Tuition")
        )
        invoice_id = invoice_response.json()["id"]
        
        # Get statement to populate cache
        response1 = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert response1.status_code == HTTPStatus.OK
        assert response1.json()["total_paid"]["amount_cents"] == 0
        assert response1.json()["total_outstanding"]["amount_cents"] == 10000
        
        # Create payment - should invalidate cache
        await authenticated_client.post(
            "/payments/",
            json=create_payment_data(student_id, 5000, invoice_id, imputation_amount=5000, currency="USD", payment_method=PaymentMethod.CASH)
        )
        
        # Get statement again - should reflect payment
        response2 = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert response2.status_code == HTTPStatus.OK
        assert response2.json()["total_paid"]["amount_cents"] == 5000
        assert response2.json()["total_outstanding"]["amount_cents"] == 5000
    
    async def test_cache_invalidated_on_payment_deletion(self, authenticated_client: AsyncClient):
        """Test cache invalidation when deleting a payment."""
        # Setup
        school_response = await authenticated_client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        student_response = await authenticated_client.post(
            "/students/",
            json=create_student_data("Frank", school_id)
        )
        student_id = student_response.json()["id"]
        
        # Create invoice
        invoice_response = await authenticated_client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 10000, currency="USD", description="Tuition")
        )
        invoice_id = invoice_response.json()["id"]
        
        # Create payment
        payment_response = await authenticated_client.post(
            "/payments/",
            json=create_payment_data(student_id, 5000, invoice_id, imputation_amount=5000, currency="USD", payment_method=PaymentMethod.CASH)
        )
        payment_id = payment_response.json()["id"]
        
        # Get statement to populate cache
        response1 = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert response1.status_code == HTTPStatus.OK
        assert response1.json()["total_paid"]["amount_cents"] == 5000
        
        # Delete payment - should invalidate cache
        await authenticated_client.delete(f"/payments/{payment_id}")
        
        # Get statement again - should show zero paid
        response2 = await authenticated_client.get(f"/account-statements/students/{student_id}")
        assert response2.status_code == HTTPStatus.OK
        assert response2.json()["total_paid"]["amount_cents"] == 0
        assert response2.json()["total_outstanding"]["amount_cents"] == 10000
    
    async def test_school_cache_invalidated_on_payment(self, authenticated_client: AsyncClient):
        """Test that school cache is invalidated when payment is made."""
        # Setup
        school_response = await authenticated_client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        student_response = await authenticated_client.post(
            "/students/",
            json=create_student_data("Grace", school_id)
        )
        student_id = student_response.json()["id"]
        
        # Create invoice
        invoice_response = await authenticated_client.post(
            "/invoices/",
            json=create_invoice_data(student_id, 10000, currency="USD", description="Tuition")
        )
        invoice_id = invoice_response.json()["id"]
        
        # Get school statement to populate cache
        response1 = await authenticated_client.get(f"/account-statements/schools/{school_id}")
        assert response1.status_code == HTTPStatus.OK
        assert response1.json()["total_paid"]["amount_cents"] == 0
        
        # Create payment - should invalidate school cache
        await authenticated_client.post(
            "/payments/",
            json=create_payment_data(student_id, 10000, invoice_id, imputation_amount=10000, currency="USD", payment_method=PaymentMethod.BANK_TRANSFER)
        )
        
        # Get school statement again - should reflect payment
        response2 = await authenticated_client.get(f"/account-statements/schools/{school_id}")
        assert response2.status_code == HTTPStatus.OK
        assert response2.json()["total_paid"]["amount_cents"] == 10000
        assert response2.json()["total_outstanding"]["amount_cents"] == 0


class TestCacheWithMultipleStudents:
    """Test cache behavior with multiple students to ensure proper isolation."""
    
    async def test_cache_isolated_per_student(self, authenticated_client: AsyncClient):
        """Test that cache is properly isolated between different students."""
        # Setup school
        school_response = await authenticated_client.post("/schools/", json=create_school_data("Test School"))
        school_id = school_response.json()["id"]
        
        # Create two students
        student1_response = await authenticated_client.post(
            "/students/",
            json=create_student_data("Student 1", school_id)
        )
        student1_id = student1_response.json()["id"]
        
        student2_response = await authenticated_client.post(
            "/students/",
            json=create_student_data("Student 2", school_id)
        )
        student2_id = student2_response.json()["id"]
        
        # Create invoices for both students
        await authenticated_client.post(
            "/invoices/",
            json=create_invoice_data(student1_id, 10000, currency="USD", description="Student 1 invoice")
        )
        
        await authenticated_client.post(
            "/invoices/",
            json=create_invoice_data(student2_id, 20000, currency="USD", description="Student 2 invoice")
        )
        
        # Get both statements to populate cache
        response1 = await authenticated_client.get(f"/account-statements/students/{student1_id}")
        response2 = await authenticated_client.get(f"/account-statements/students/{student2_id}")
        
        assert response1.json()["total_invoiced"]["amount_cents"] == 10000
        assert response2.json()["total_invoiced"]["amount_cents"] == 20000
        
        # Create new invoice for student 1 - should only invalidate student 1 cache
        await authenticated_client.post(
            "/invoices/",
            json=create_invoice_data(student1_id, 5000, currency="USD", description="Student 1 second invoice")
        )
        
        # Student 1 should have updated total
        response1_updated = await authenticated_client.get(f"/account-statements/students/{student1_id}")
        assert response1_updated.json()["total_invoiced"]["amount_cents"] == 15000
        
        # Student 2 should still have same total (could be from cache or fresh query)
        response2_same = await authenticated_client.get(f"/account-statements/students/{student2_id}")
        assert response2_same.json()["total_invoiced"]["amount_cents"] == 20000
