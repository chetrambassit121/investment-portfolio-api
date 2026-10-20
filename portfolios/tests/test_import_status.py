import pytest

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from portfolios.models import ImportLog


'''
@pytest.fixture creates reusable test objects.
APIClient() simulates HTTP requests without starting a Django server.
force_authenticate() simulates an authenticated user.
@pytest.mark.django_db allows the test to access its isolated PostgreSQL test database.
assert verifies that the API returns the expected result.
'''

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(db):
    User = get_user_model()

    user = User.objects.create_user(
        username="testuser",
        password="testpassword123"
    )

    client = APIClient()
    client.force_authenticate(user=user)

    return client


@pytest.mark.django_db
def test_import_status_no_imports(authenticated_client):
    """
    Test when no S3 imports have been recorded.
    """

    response = authenticated_client.get(
        "/api/import-status/"
    )

    assert response.status_code == 200
    assert response.data["status"] == "never_run"
    assert response.data["message"] == (
        "No S3 imports recorded yet."
    )


@pytest.mark.django_db
def test_import_status_requires_authentication(api_client):
    """
    Test that anonymous users cannot access import status.
    """

    response = api_client.get(
        "/api/import-status/"
    )

    assert response.status_code in [401, 403]


@pytest.mark.django_db
def test_import_status_success(authenticated_client):
    """
    Verify that a successful S3 import
    returns the correct status and counts.
    """

    ImportLog.objects.create(
        status="success",
        source="AWS S3",
        total_records=3,
        created_count=3,
        updated_count=0,
    )

    response = authenticated_client.get(
        "/api/import-status/"
    )

    assert response.status_code == 200
    assert response.data["status"] == "success"
    assert response.data["total_records"] == 3
    assert response.data["created_count"] == 3
    assert response.data["updated_count"] == 0


@pytest.mark.django_db
def test_import_status_failed(authenticated_client):
    """
    Verify that failed imports are
    correctly reported by the API.
    """

    ImportLog.objects.create(
        status="failed",
        source="AWS S3",
        total_records=0,
        error_message="Unable to read S3 object",
    )

    response = authenticated_client.get(
        "/api/import-status/"
    )

    assert response.status_code == 200
    assert response.data["status"] == "failed"


@pytest.mark.django_db
def test_import_status_returns_latest(authenticated_client):
    """
    Verify that the API returns the
    most recent import record.
    """

    ImportLog.objects.create(
        status="failed",
        total_records=0,
    )

    latest_import = ImportLog.objects.create(
        status="success",
        total_records=5,
        created_count=2,
        updated_count=3,
    )

    response = authenticated_client.get(
        "/api/import-status/"
    )

    assert response.status_code == 200
    assert response.data["id"] == latest_import.id
    assert response.data["status"] == "success"
    assert response.data["total_records"] == 5


@pytest.mark.django_db
def test_import_status_response_fields(authenticated_client):
    """
    Verify that the API returns the
    expected import metadata.
    """

    ImportLog.objects.create(
        status="success",
        source="AWS S3",
        total_records=10,
        created_count=7,
        updated_count=3,
    )

    response = authenticated_client.get(
        "/api/import-status/"
    )

    assert response.status_code == 200

    expected_fields = [
        "id",
        "status",
        "source",
        "total_records",
        "created_count",
        "updated_count",
        "started_at",
        "completed_at",
    ]

    for field in expected_fields:
        assert field in response.data