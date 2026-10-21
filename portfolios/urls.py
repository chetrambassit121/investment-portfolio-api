from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PortfolioViewSet,
    AssetViewSet,
    TransactionViewSet,
    portfolio_summary,
    ImportStatusView,
    QueuePortfolioImportView
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
    path(
        "portfolios/import/",
        QueuePortfolioImportView.as_view(),
        name="queue-portfolio-import",
    ),
    path("", include(router.urls)),
]