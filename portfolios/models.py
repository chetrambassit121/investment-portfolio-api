from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Portfolio(models.Model):
    name = models.CharField(max_length=200)
    fund_type = models.CharField(max_length=100)
    currency = models.CharField(max_length=3, default="USD")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Asset(models.Model):
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name="assets"
    )
    name = models.CharField(max_length=200)
    asset_type = models.CharField(max_length=100)
    market_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))]
    )

    def __str__(self):
        return self.name


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("BUY", "Buy"),
        ("SELL", "Sell"),
    ]

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="transactions"
    )
    transaction_type = models.CharField(
        max_length=4,
        choices=TRANSACTION_TYPES
    )
    amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))]
    )
    transaction_date = models.DateField()

    def __str__(self):
        return f"{self.transaction_type} - {self.asset.name}"


class ImportLog(models.Model):
    '''
        Field:	                Purpose:
        status	                Running, success, or failed
        source	                Where the data originated
        total_records	        Records processed
        created_count	        New portfolios created
        updated_count	        Existing portfolios updated
        started_at	            Import start time
        completed_at	        Import completion time
        error_message	        Failure details for internal debugging
    '''

    # STATUS_CHOICES = [
    #     ("running", "Running"),
    #     ("success", "Success"),
    #     ("failed", "Failed"),
    # ]

    # status = models.CharField(
    #     max_length=20,
    #     choices=STATUS_CHOICES,
    #     default="running",
    # )

    STATUS_CHOICES = [
    ("queued", "Queued"),
    ("running", "Running"),
    ("success", "Success"),
    ("failed", "Failed"),
]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="queued",
    )

    source = models.CharField(
        max_length=100,
        default="AWS S3",
    )

    total_records = models.IntegerField(default=0)
    created_count = models.IntegerField(default=0)
    updated_count = models.IntegerField(default=0)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    error_message = models.TextField(blank=True)

    def __str__(self):
        return f"{self.status} - {self.started_at}"