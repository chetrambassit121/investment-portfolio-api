import pytest

from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient

from portfolios.models import Portfolio, Asset


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def portfolio(db):
    return Portfolio.objects.create(
        name="Test Investment Fund",
        fund_type="Private Equity",
        currency="USD",
    )


@pytest.mark.django_db
def test_create_portfolio(api_client):
    response = api_client.post(
        reverse("portfolio-list"),
        {
            "name": "New Growth Fund",
            "fund_type": "Private Equity",
            "currency": "USD",
        },
        format="json",
    )

    assert response.status_code == 201
    assert Portfolio.objects.filter(
        name="New Growth Fund"
    ).exists()


@pytest.mark.django_db
def test_get_portfolios(api_client, portfolio):
    response = api_client.get(
        reverse("portfolio-list")
    )

    assert response.status_code == 200
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_create_asset(api_client, portfolio):
    response = api_client.post(
        reverse("asset-list"),
        {
            "portfolio": portfolio.id,
            "name": "Office Property",
            "asset_type": "Real Estate",
            "market_value": "5000000.00",
        },
        format="json",
    )

    assert response.status_code == 201
    assert Asset.objects.filter(
        name="Office Property"
    ).exists()


@pytest.mark.django_db
def test_negative_asset_value_rejected(api_client, portfolio):
    response = api_client.post(
        reverse("asset-list"),
        {
            "portfolio": portfolio.id,
            "name": "Invalid Asset",
            "asset_type": "Real Estate",
            "market_value": "-100.00",
        },
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_portfolio_summary(api_client, portfolio):
    Asset.objects.create(
        portfolio=portfolio,
        name="Asset A",
        asset_type="Private Equity",
        market_value=Decimal("2000000.00"),
    )

    Asset.objects.create(
        portfolio=portfolio,
        name="Asset B",
        asset_type="Private Equity",
        market_value=Decimal("3000000.00"),
    )

    response = api_client.get(
        reverse("portfolio-summary")
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert (
        Decimal(response.data["results"][0]["total_value"])
        == Decimal("5000000.00")
    )