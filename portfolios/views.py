from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def portfolio_list(request):
    portfolios = [
        {
            "id": 1,
            "name": "Private Equity Fund A",
            "total_value": 15000000,
            "currency": "USD",
        },
        {
            "id": 2,
            "name": "Real Estate Fund B",
            "total_value": 25000000,
            "currency": "USD",
        },
    ]

    return Response({
        "count": len(portfolios),
        "results": portfolios,
    })
