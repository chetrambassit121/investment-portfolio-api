from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PortfolioViewSet,
    AssetViewSet,
    TransactionViewSet,
    portfolio_summary,
    ImportStatusView,
)

router = DefaultRouter()

router.register(
    r"portfolios",
    PortfolioViewSet,
    basename="portfolio"
)

router.register(
    r"assets",
    AssetViewSet,
    basename="asset"
)

router.register(
    r"transactions",
    TransactionViewSet,
    basename="transaction"
)

urlpatterns = [
    path(
        "reports/portfolio-summary/",
        portfolio_summary,
        name="portfolio-summary"
    ),
    path(
        "import-status/",
        ImportStatusView.as_view(),
        name="import-status",
    ),
    path("", include(router.urls)),
]