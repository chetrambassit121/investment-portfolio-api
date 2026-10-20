import json
from io import BytesIO
from unittest.mock import patch

import pytest
from django.core.management import call_command, CommandError

from portfolios.models import Portfolio

'''
These four tests check:
Test	        What we're verifying
Create	        New S3 records are inserted into PostgreSQL
Update	        Existing records are updated without duplicates
Invalid JSON	Malformed S3 data is rejected
Rollback	    A failed import leaves no partial database changes
'''


@pytest.mark.django_db
@patch(
    "portfolios.management.commands.import_s3_portfolios.boto3.client"
)
def test_import_creates_portfolios(mock_boto_client):

    sample_data = [
        {
            "name": "Test Equity Fund",
            "fund_type": "Private Equity",
            "currency": "USD",
        }
    ]

    mock_s3 = mock_boto_client.return_value

    mock_s3.get_object.return_value = {
        "Body": BytesIO(json.dumps(sample_data).encode())
    }

    call_command("import_s3_portfolios")

    assert Portfolio.objects.filter(
        name="Test Equity Fund"
    ).exists()

    assert Portfolio.objects.count() == 1


@pytest.mark.django_db
@patch(
    "portfolios.management.commands.import_s3_portfolios.boto3.client"
)
def test_import_updates_existing_portfolio(mock_boto_client):

    Portfolio.objects.create(
        name="Test Equity Fund",
        fund_type="Private Equity",
        currency="USD",
    )

    sample_data = [
        {
            "name": "Test Equity Fund",
            "fund_type": "Infrastructure",
            "currency": "EUR",
        }
    ]

    mock_s3 = mock_boto_client.return_value

    mock_s3.get_object.return_value = {
        "Body": BytesIO(json.dumps(sample_data).encode())
    }

    call_command("import_s3_portfolios")

    portfolio = Portfolio.objects.get(name="Test Equity Fund")

    assert portfolio.fund_type == "Infrastructure"
    assert portfolio.currency == "EUR"
    assert Portfolio.objects.count() == 1


@pytest.mark.django_db
@patch(
    "portfolios.management.commands.import_s3_portfolios.boto3.client"
)
def test_import_invalid_json(mock_boto_client):

    mock_s3 = mock_boto_client.return_value

    mock_s3.get_object.return_value = {
        "Body": BytesIO(b"invalid-json")
    }

    with pytest.raises(CommandError):
        call_command("import_s3_portfolios")


@pytest.mark.django_db
@patch(
    "portfolios.management.commands.import_s3_portfolios.boto3.client"
)
def test_import_rolls_back_on_invalid_record(mock_boto_client):

    sample_data = [
        {
            "name": "Valid Fund",
            "fund_type": "Private Equity",
            "currency": "USD",
        },
        {
            "name": "Broken Fund",
            "fund_type": "Real Estate",
        },
    ]

    mock_s3 = mock_boto_client.return_value

    mock_s3.get_object.return_value = {
        "Body": BytesIO(json.dumps(sample_data).encode())
    }

    with pytest.raises(CommandError):
        call_command("import_s3_portfolios")

    assert Portfolio.objects.count() == 0