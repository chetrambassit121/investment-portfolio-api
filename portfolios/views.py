from django.utils import timezone
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

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ImportLog
from .serializers import ImportLogSerializer

from botocore.exceptions import BotoCoreError, ClientError
from django.core.exceptions import ImproperlyConfigured
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from portfolios.services.sqs_service import send_portfolio_import_message

logger = logging.getLogger(__name__)
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




class ImportStatusView(APIView):
    '''
        1. Django queries PostgreSQL for the latest import record.
        2. The serializer converts the record into JSON.
        3. Django REST Framework returns the result to an authenticated user.
    '''
    permission_classes = [IsAuthenticated]

    def get(self, request):
        latest_import = (
            ImportLog.objects
            .order_by("-started_at", "-id")
            .first()
        )

        if latest_import is None:
            return Response({
                "status": "never_run",
                "message": "No S3 imports recorded yet.",
            })

        serializer = ImportLogSerializer(latest_import)

        return Response(serializer.data)


class QueuePortfolioImportView(APIView):
    """
    Queue an S3 portfolio import job using AWS SQS.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):

        import_log = ImportLog.objects.create(
            status="queued",
            source="AWS S3",
        )

        try:
            message_id = send_portfolio_import_message(
                import_id=import_log.id
            )

        except (ClientError, BotoCoreError, ImproperlyConfigured):
            logger.exception(
                "Unable to queue portfolio import job"
            )

            import_log.status = "failed"
            import_log.error_message = (
                "Unable to queue import job."
            )
            import_log.completed_at = timezone.now()
            import_log.save()

            return Response(
                {
                    "status": "error",
                    "message": "Unable to queue import job.",
                    "import_id": import_log.id,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "status": "queued",
                "message": "Portfolio import job queued successfully.",
                "import_id": import_log.id,
                "message_id": message_id,
            },
            status=status.HTTP_202_ACCEPTED,
        )
