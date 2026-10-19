import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from portfolios.models import Portfolio, Asset


class Command(BaseCommand):
    help = "Import fictional investment data from JSON"

    def handle(self, *args, **options):
        file_path = (
            Path(settings.BASE_DIR)
            / "data"
            / "investments.json"
        )

        try:
            with file_path.open("r", encoding="utf-8") as file:
                data = json.load(file)

            if not isinstance(data, list):
                raise CommandError("Expected a JSON array")

            with transaction.atomic():
                for item in data:
                    portfolio, _ = Portfolio.objects.get_or_create(
                        name=item["name"],
                        defaults={
                            "fund_type": item["fund_type"],
                            "currency": item.get("currency", "USD"),
                        },
                    )

                    for asset_data in item["assets"]:
                        value = Decimal(
                            str(asset_data["market_value"])
                        )

                        if not value.is_finite() or value < 0:
                            raise CommandError(
                                "Market value must be non-negative"
                            )

                        Asset.objects.update_or_create(
                            portfolio=portfolio,
                            name=asset_data["name"],
                            defaults={
                                "asset_type": asset_data["asset_type"],
                                "market_value": value,
                            },
                        )

            self.stdout.write(
                self.style.SUCCESS(
                    "Investment data imported successfully!"
                )
            )

        except (
            OSError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            InvalidOperation,
            ValueError,
        ) as exc:
            raise CommandError(
                f"Investment import failed: {exc}"
            ) from exc