from rest_framework import viewsets
from .models import Portfolio, Asset, Transaction
from .serializers import (
    PortfolioSerializer,
    AssetSerializer,
    TransactionSerializer,
)

from django.db.models import Sum, Count, Value, DecimalField
from django.db.models.functions import Coalesce
from rest_framework.decorators import api_view
from rest_framework.response import Response

import logging
from rest_framework import status
from rest_framework.exceptions import APIException

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter


logger = logging.getLogger("portfolios")


class PortfolioViewSet(viewsets.ModelViewSet):
    # queryset = Portfolio.objects.all()
    queryset = Portfolio.objects.all().order_by("id")
    serializer_class = PortfolioSerializer

    def perform_create(self, serializer):
        portfolio = serializer.save()

        logger.info(
            "Portfolio created: id=%s name=%s",
            portfolio.id,
            portfolio.name,
        )

    def perform_update(self, serializer):
        portfolio = serializer.save()

        logger.info(
            "Portfolio updated: id=%s",
            portfolio.id,
        )

    def perform_destroy(self, instance):
        portfolio_id = instance.id
        instance.delete()

        logger.info(
            "Portfolio deleted: id=%s",
            portfolio_id,
        )


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.select_related("portfolio").all()
    serializer_class = AssetSerializer

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
        OrderingFilter,
    ]

    filterset_fields = [
        "portfolio",
        "asset_type",
    ]

    search_fields = [
        "name",
        "asset_type",
    ]

    ordering_fields = [
        "market_value",
        "name",
        "id",
    ]

    ordering = ["id"]


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer


@api_view(["GET"])
def portfolio_summary(request):
    portfolios = (
        Portfolio.objects
        .annotate(
            asset_count=Count("assets"),
            total_value=Coalesce(
                Sum("assets__market_value"),
                Value(0),
                output_field=DecimalField(
                    max_digits=20,
                    decimal_places=2
                ),
            ),
        )
        .order_by("-total_value")
    )

    results = [
        {
            "id": portfolio.id,
            "name": portfolio.name,
            "fund_type": portfolio.fund_type,
            "asset_count": portfolio.asset_count,
            "total_value": str(portfolio.total_value),
        }
        for portfolio in portfolios
    ]

    return Response({
        "count": len(results),
        "results": results,
    })
