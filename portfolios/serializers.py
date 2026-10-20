from rest_framework import serializers
from .models import Portfolio, Asset, Transaction
from .models import ImportLog

class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = "__all__"


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = "__all__"


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"

class ImportLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportLog

        fields = [
            "id",
            "status",
            "source",
            "total_records",
            "created_count",
            "updated_count",
            "started_at",
            "completed_at",
        ]

        read_only_fields = fields
