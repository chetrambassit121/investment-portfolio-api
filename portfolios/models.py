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
