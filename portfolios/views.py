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


class PortfolioViewSet(viewsets.ModelViewSet):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer


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
