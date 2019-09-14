"""mex URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from mex import views

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("blocks/", views.BlockListView.as_view(), name="blocks"),
    path("txs/", views.TransactionListView.as_view(), name="transactions"),
    path("addrs/", views.AddressListView.as_view(), name="addresses"),
    path("streams/", views.StreamListView.as_view(), name="streams"),
    path("tokens/", views.TokenListView.as_view(), name="tokens"),
    path("status/", views.StatusView.as_view(), name="status"),
    path("block/<str:hash>", views.BlockDetailView.as_view(), name="block-detail"),
    path(
        "tx/<str:hash>",
        views.TransactionDetailView.as_view(),
        name="transaction-detail",
    ),
    path(
        "addr/<str:address>", views.AddressDetailView.as_view(), name="address-detail"
    ),
    path("stream/<str:stream>", views.StreamDetailView.as_view(), name="stream-detail"),
    path("token/<str:token>", views.TokenDetailView.as_view(), name="token-detail"),
    path("table/blocks", views.TableBlocks.as_view(), name="table-blocks"),
    path(
        "table/transactions",
        views.TableTransactions.as_view(),
        name="table-transactions",
    ),
    path("admin/", admin.site.urls),
]
