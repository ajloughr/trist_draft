from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import auction_user, auction_manager
from django.conf import settings

import json
from django.core.serializers.json import DjangoJSONEncoder
from django.core import serializers

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import channels.layers

from django.shortcuts import get_object_or_404

# @receiver(post_save, sender=auction_manager)
# def update_auction_table(sender, instance, **kwargs):
#     print("Auction Manager Update Received!")
    
#     # prev_auction_manager_active_bidder = auction_manager.objects.get(pk=1).active_bidder
#     # new_auction_manager_active_bidder = instance.active_bidder

#     # if instance.pk and prev_auction_manager_active_bidder != new_auction_manager_active_bidder:

#     channel_layer = channels.layers.get_channel_layer()
#     group_name = settings.AUCTION_UPDATE_GROUP

#     new_auction_user_list = auction_user.objects.all().order_by('draft_order')
#     #new_auction_user_list_s = json.dumps(list(new_auction_user_list), cls=DjangoJSONEncoder)
#     new_auction_user_list_s = serializers.serialize('json', new_auction_user_list)

#     new_auction_manager = auction_manager.objects.filter(pk=1)
#     new_auction_manager_s = serializers.serialize('json', new_auction_manager)

#     async_to_sync(channel_layer.group_send)(
#         group_name,
#         {
#             'type': 'active_bidder_update',
#             'auction_table_data': new_auction_user_list_s,
#             'auction_manager_data' : new_auction_manager_s
#             #also adds source user in consumer
#         }
#     )
#     # else: 
#     #     print("Not updating tables because active bidder didnt change")
