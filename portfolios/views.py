from rest_framework import viewsets
from .models import Portfolio, Asset, Transaction
from .serializers import (
    PortfolioSerializer,
    AssetSerializer,
    TransactionSerializer,
)


class PortfolioViewSet(viewsets.ModelViewSet):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
