from django.urls import path
from .views import portfolio_list

urlpatterns = [
    path("", portfolio_list, name="portfolio-list"),
]