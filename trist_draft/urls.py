"""trist_draft URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import path, include
from django.conf.urls import url

from . import views
from trist_draft.apps.auction_table.views import (
    # old_auction_table_view,
    # new_bid_view,
    # return_to_auction,
    # ajax_auction_table,
    # ajax_new_bid_view,
    # check_ajax_stuff,
    auction_table_view,
)
from trist_draft.apps.accounts.views import login_view, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('old_auction/', old_auction_table_view),
    path('login/', login_view),
    path('logout/', logout_view),
    # path('new-bid/',new_bid_view, name="new-bid"),

    # path('auction/return-to-auction/', return_to_auction, name="return-to-auction"),

    # path('ajax_table/',ajax_auction_table, name="ajax_table"),
    # url('ajax_bid_menu/', ajax_new_bid_view, name='ajax_bid_form'),
    # url('ajax_bid_menu_check/', check_ajax_stuff, name='check_ajax_stuff'),

    path('auction/',auction_table_view, name="auction"),

    path('', include('trist_draft.apps.public.urls'))
       
]
