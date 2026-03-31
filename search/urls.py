from django.urls import path
from . import views

urlpatterns = [
    path('query/', views.QueryView.as_view(), name='search-query'),
    path('history/', views.QueryHistoryView.as_view(), name='search-history'),
]