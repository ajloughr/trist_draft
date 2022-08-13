from django.conf import settings
from asgiref.sync import async_to_sync
from channels.consumer import SyncConsumer
import json
from channels.generic.websocket import WebsocketConsumer
from .models import auction_user, auction_manager, nfl_player, drafted_player
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.db.models import Max
from django.db.models.signals import post_save
from django.core import serializers
import channels.layers
from itertools import chain

class AuctionConsumer(WebsocketConsumer):

    def websocket_connect(self, event):
        # self.accept({
        #     'type': 'websocket.accept'
        # })

        # Join group
        async_to_sync(self.channel_layer.group_add)(
            settings.AUCTION_UPDATE_GROUP,
            self.channel_name
        )

        async_to_sync(self.channel_layer.group_add)(
            settings.PLAYER_SEARCH_GROUP,
            self.channel_name
        )
        
        self.accept()



    def websocket_disconnect(self, event):
        # Leave group
        async_to_sync(self.channel_layer.group_discard)(
            settings.AUCTION_UPDATE_GROUP,
            self.channel_name
        )

        async_to_sync(self.channel_layer.group_discard)(
            settings.PLAYER_SEARCH_GROUP,
            self.channel_name
        )
    
    # Receive active bidder update
    def active_bidder_update(self, event):
        # source_user_id = self.scope["user"].id
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'type': 'active_bidder_update',
            'auction_table_data': event['auction_table_data'],
            'auction_manager_data': event['auction_manager_data'],
            'update_target':event['update_target']
            # 'source_user_id': source_user_id
        }))

    # Receive player search results
    def player_search_results(self, event):
        # source_user_id = self.scope["user"].id
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'type': 'player_search_results',
            'search_result_data': event['search_result_data'],
            'searching_team': event['searching_team'],
            # 'source_user_id': source_user_id
        }))

    # Receive rfa results
    def user_rfa_results(self, event):
        self.send(text_data=json.dumps({
            'type': 'user_rfa_results',
            'team_name': event['team_name'],
            'user_rfa_results_data': event['user_rfa_results_data'],
        }))


    # Receive end of auction info
    def auction_end_confirmation(self, event):
        # source_user_id = self.scope["user"].id
        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'type': 'auction_end_confirmation',
            'confirmation_step': event['confirmation_step'],
            'auction_winner':event['auction_winner'],
            'initiated_auction':event['initiated_auction'],
            'winning_player_name':event['winning_player_name'],
            'winning_contract_years':event['winning_contract_years'],
            'winning_contract_cost':event['winning_contract_cost']
            # 'source_user_id': source_user_id
        }))

    # Receive message from WebSocket
    def receive(self, text_data):
        # source_user_id = self.scope["user"].id
        # print("Current User Id: " + str(source_user_id))
        # source_auction_user = get_object_or_404(auction_user,user=source_user_id)
        # print("Current User: " + str(source_auction_user))


        try:
            text_data_json = json.loads(text_data)
            #print("Success: " + str(text_data_json))
        except Exception as e:
            print("Failure: " + str(text_data))
            print(e)
            return
        
        if "new_bid" in text_data_json:
            print("Consumer received new bid")
            submit_new_bid(text_data_json)
        elif "drop_out" in text_data_json:
            print("Consumer received drop out request")
            drop_out_user(text_data_json)
        elif "pass" in text_data_json:
            print("Consumer received pass request")
            pass_user(text_data_json)
        elif "refresh" in text_data_json:
            print("Consumer received refresh request")
            refresh_auction_table(text_data_json['target'])
        elif "reset_users" in text_data_json:
            print("Consumer received reset users request")
            reset_auction_table()
        elif "reset_drop_outs" in text_data_json:
            print("Consumer received reset drop outs request")
            reset_drop_outs()
        elif "reset_manager" in text_data_json:
            print("Consumer received reset manager request")
            reset_auction_manager()
        elif "new_bid_start" in text_data_json:
            print("Consumer received new start request")
            start_new_auction_at_bidder(text_data_json,True)
        elif "player_search_text" in text_data_json:
            print("Consumer received new search player request")
            get_player_search_results(text_data_json)
        elif "submitted_player_name" in text_data_json:
            print("Consumer received new player for auction")
            submit_auction_player(text_data_json)
        elif "drop_out_player_selection" in text_data_json:
            print("Consumer received drop out of player selection")
            drop_out_of_or_pass_player_selection(text_data_json,True)
        elif "pass_player_selection" in text_data_json:
            print("Consumer received pass player selection")
            drop_out_of_or_pass_player_selection(text_data_json,False)
        elif "results_response" in text_data_json:
            print("Consumer received auction results response")
            receive_auction_results_response(text_data_json)
        elif "get_rfas_for_user" in text_data_json:
            print("Consumer received get rfas for user request")
            get_rfas_for_user(text_data_json)
        # elif "rfa_owner_match_1_response" in text_data_json:
        #     print("Consumer received rfa owner confirm 1")
        #     rfa_owner_match_1_receive_response(text_data_json)
        elif "bathroom_mode_toggled" in text_data_json:
            print("Consumer received bathroom mode toggle")
            toggle_bathroom_mode(text_data_json['team_name'],text_data_json['bathroom_mode_state'])
        elif "update_rfas_remaining" in text_data_json:
            print("Consumer update rfas remaining")
            update_rfas_remaining()

def toggle_bathroom_mode(toggle_team_name,bathroom_mode_state):
    user_team_model = get_object_or_404(auction_user,team_name=toggle_team_name)
    user_team_model.bathroom_mode_enabled = bathroom_mode_state

    user_team_model.save()

    refresh_auction_table('all')


def update_rfas_remaining():

    all_auction_users = auction_user.objects.all()

    for this_auction_user in all_auction_users:
        this_auction_user.rfas_remaining = len(this_auction_user.current_rfa_list)
        this_auction_user.save()
    


def update_auction_table(refresh_target):
    print("Auction Manager Update Received!")
    
    channel_layer = channels.layers.get_channel_layer()
    group_name = settings.AUCTION_UPDATE_GROUP

    new_auction_user_list = auction_user.objects.all().order_by('draft_order')
    new_auction_user_list_s = serializers.serialize('json', new_auction_user_list)

    new_auction_manager = auction_manager.objects.filter(pk=1)
    new_auction_manager_s = serializers.serialize('json', new_auction_manager)

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'active_bidder_update',
            'auction_table_data': new_auction_user_list_s,
            'auction_manager_data' : new_auction_manager_s,
            'update_target':refresh_target
        }
    )

def get_rfas_for_user(get_rfa_for_user_data):
    print("Getting rfas for user: " + get_rfa_for_user_data['team_name'])

    user_team_model = get_object_or_404(auction_user,team_name=get_rfa_for_user_data['team_name'])
    user_rfa_index_list = user_team_model.current_rfa_list
    #print("User RFA Index List: " + str(user_rfa_index_list))
    
    user_rfas = nfl_player.objects.filter(player_id__in=user_rfa_index_list)
    
    user_rfas_s = serializers.serialize('json', user_rfas)

    channel_layer = channels.layers.get_channel_layer()
    group_name = settings.AUCTION_UPDATE_GROUP

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'user_rfa_results',
            'team_name':get_rfa_for_user_data['team_name'],
            'user_rfa_results_data': user_rfas_s,
        }
    )

def receive_auction_results_response(results_response_data):
    print("Processing auction results: " + str(results_response_data))
    results_response_type = results_response_data['results_response']
    
    current_auction_manager = get_object_or_404(auction_manager,pk=1)
    initiated_auction_user_object = get_object_or_404(auction_user,draft_order=current_auction_manager.initiated_auction)
    draft_winner_object = get_object_or_404(auction_user,draft_order=current_auction_manager.team_with_highest_bid)

    if results_response_type == 'rfa_owner_match_1_rejected' or results_response_type == 'rfa_owner_match_2_rejected':
        print( results_response_type + ", confirming winning team")
        
        #loop through rfas for user who initiated auction, find the player that was just auctioned and remove them
        for rfa_index in initiated_auction_user_object.current_rfa_list:
            
            current_rfa_object = get_object_or_404(nfl_player,player_id=rfa_index)

            #make sure we have the correct player and remove them from the users RFA list
            if  (current_rfa_object.full_name == current_auction_manager.player_for_auction_name and 
                current_rfa_object.team == current_auction_manager.player_for_auction_team and 
                current_rfa_object.position == current_auction_manager.player_for_auction_position):

                initiated_auction_user_object.current_rfa_list.remove(rfa_index)
                initiated_auction_user_object.save()

        save_drafted_player(draft_winner_object.team_name,current_auction_manager.player_for_auction_name,current_auction_manager.player_for_auction_team,current_auction_manager.player_for_auction_position,False)

        send_rfa_auction_end(draft_winner_object.team_name,current_auction_manager.initiated_auction)

        next_bid_initiator_draft_order = get_next_bidder(current_auction_manager.initiated_auction,current_auction_manager.initiated_auction,'rfa',True)

        new_start_data = {
            'new_bid_start': next_bid_initiator_draft_order,
            'new_bid_type' : 'rfa'
        }

        start_new_auction_at_bidder(new_start_data,False)

    elif results_response_type == 'rfa_owner_match_1_matched':
        print("RFA Match Matched, offering bid winner chance to raise")

        current_auction_manager.auction_state = 'rfa_bid_winner_offer_raise'
        current_auction_manager.save()

        winning_player_name = current_auction_manager.player_for_auction_name
        winning_contract_years = current_auction_manager.highest_bid
        winning_contract_cost = current_auction_manager.highest_contract_years

        channel_layer = channels.layers.get_channel_layer()
        group_name = settings.AUCTION_UPDATE_GROUP

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'auction_end_confirmation',
                'confirmation_step': 'rfa_bid_winner_offer_raise',
                'auction_winner':draft_winner_object.team_name,
                'initiated_auction':initiated_auction_user_object.team_name,
                'winning_player_name':winning_player_name,
                'winning_contract_years':winning_contract_years,
                'winning_contract_cost':winning_contract_cost
            }
        )
    elif results_response_type == 'rfa_bid_winner_raised':
        print("RFA winner raised, offering owner chance to match")
        
        raised_bid = int(results_response_data["raise_bid"])
        print("Raised bid: " + str(raised_bid))
        #update the highest bid with the raised number
        draft_winner_object.current_bid = raised_bid
        current_auction_manager.highest_bid = raised_bid
        current_auction_manager.auction_state = 'rfa_owner_match_request_2'

        draft_winner_object.save()
        current_auction_manager.save()

        winning_player_name = current_auction_manager.player_for_auction_name
        winning_contract_years = current_auction_manager.highest_bid
        winning_contract_cost = current_auction_manager.highest_contract_years

        channel_layer = channels.layers.get_channel_layer()
        group_name = settings.AUCTION_UPDATE_GROUP

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'auction_end_confirmation',
                'confirmation_step': 'rfa_owner_match_request_2',
                'auction_winner':draft_winner_object.team_name,
                'initiated_auction':initiated_auction_user_object.team_name,
                'winning_player_name':winning_player_name,
                'winning_contract_years':winning_contract_years,
                'winning_contract_cost':winning_contract_cost
            }
        )

        refresh_auction_table("all")

    elif results_response_type == 'rfa_bid_winner_dropped_out' or results_response_type == 'rfa_owner_match_2_matched':
        print(results_response_type + ", giving player to owner for highest bid")
        
        #loop through rfas for user who initiated auction, find the player that was just auctioned and remove them
        for rfa_index in initiated_auction_user_object.current_rfa_list:
            
            current_rfa_object = get_object_or_404(nfl_player,player_id=rfa_index)

            if  (current_rfa_object.full_name == current_auction_manager.player_for_auction_name and 
                current_rfa_object.team == current_auction_manager.player_for_auction_team and 
                current_rfa_object.position == current_auction_manager.player_for_auction_position):

                initiated_auction_user_object.current_rfa_list.remove(rfa_index)
                initiated_auction_user_object.save()

                initiated_auction_user_object = get_object_or_404(auction_user,draft_order=current_auction_manager.initiated_auction)
                initiated_auction_user_object.rfas_remaining = len(initiated_auction_user_object.current_rfa_list)
                initiated_auction_user_object.save()

        save_drafted_player(initiated_auction_user_object.team_name,current_auction_manager.player_for_auction_name,current_auction_manager.player_for_auction_team,current_auction_manager.player_for_auction_position,False)

        send_rfa_auction_end(initiated_auction_user_object.team_name,current_auction_manager.initiated_auction)

        next_bid_initiator_draft_order = get_next_bidder(current_auction_manager.initiated_auction,current_auction_manager.initiated_auction,'rfa',True)

        new_start_data = {
            'new_bid_start': next_bid_initiator_draft_order,
            'new_bid_type' : 'rfa'
        }

        start_new_auction_at_bidder(new_start_data,False)
    elif results_response_type == 'ufa_confirmed':
        print( results_response_type + ", confirming winning team")
        
        #check to see if this player is manually entered
        nfl_player_check = nfl_player.objects.filter(full_name=current_auction_manager.player_for_auction_name,team=current_auction_manager.player_for_auction_team,position=current_auction_manager.player_for_auction_position)
        #print("nfl_player_check: " + str(nfl_player_check))
        if len(nfl_player_check) > 0:
            drafted_player_is_manual = False
        else:
            drafted_player_is_manual = True


        save_drafted_player(draft_winner_object.team_name,current_auction_manager.player_for_auction_name,current_auction_manager.player_for_auction_team,current_auction_manager.player_for_auction_position,drafted_player_is_manual)

        send_ufa_auction_end(draft_winner_object.team_name,current_auction_manager.initiated_auction)

        next_bid_initiator_draft_order = get_next_bidder(current_auction_manager.initiated_auction,current_auction_manager.initiated_auction,'ufa',True)

        new_start_data = {
            'new_bid_start': next_bid_initiator_draft_order,
            'new_bid_type' : 'ufa'
        }

        start_new_auction_at_bidder(new_start_data,False)

def send_ufa_auction_end(bid_winner,initiated_auction):
    print("UFA Auction is ending")

    current_auction_manager = get_object_or_404(auction_manager,pk=1) 
    current_auction_manager.auction_state = 'ufa_auction_end'
    current_auction_manager.save()

    channel_layer = channels.layers.get_channel_layer()
    group_name = settings.AUCTION_UPDATE_GROUP

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'auction_end_confirmation',
            'confirmation_step': 'ufa_auction_end',
            'auction_winner':bid_winner,
            'initiated_auction':initiated_auction,
            'winning_player_name':None,
            'winning_contract_years':None,
            'winning_contract_cost':None
        }
    )

#this seems unneccisary, probably can move into function or move all sends to this function
def send_rfa_auction_end(bid_winner,initiated_auction):
    print("RFA Auction is ending")

    current_auction_manager = get_object_or_404(auction_manager,pk=1) 
    current_auction_manager.auction_state = 'rfa_auction_end'
    current_auction_manager.save()

    channel_layer = channels.layers.get_channel_layer()
    group_name = settings.AUCTION_UPDATE_GROUP

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'auction_end_confirmation',
            'confirmation_step': 'rfa_auction_end',
            'auction_winner':bid_winner,
            'initiated_auction':initiated_auction,
            'winning_player_name':None,
            'winning_contract_years':None,
            'winning_contract_cost':None
        }
    )

def drop_out_of_or_pass_player_selection(submitted_player_data,is_drop_out):
    reset_auction_table()

    current_auction_manager = get_object_or_404(auction_manager,pk=1)

    if submitted_player_data['admin_bid_override']:
        source_auction_user = get_object_or_404(auction_user,draft_order=current_auction_manager.active_bidder)
    else:
        source_auction_user = get_object_or_404(auction_user,team_name=submitted_player_data['team_name'])

    #modify user if drop out is true
    if is_drop_out == True:
        source_auction_user.dropped_out_of_selection = True
    
    source_auction_user.save()

    #start a bid for the next person
    new_bid_start = get_next_bidder(current_auction_manager.active_bidder,current_auction_manager.initiated_auction,current_auction_manager.auction_type,True)

    current_auction_manager.active_bidder = new_bid_start
    current_auction_manager.initiated_auction = new_bid_start

    current_auction_manager.save()

    update_auction_table('all')

def save_drafted_player(winning_team,drafted_player_full_name,drafted_player_team,drafted_player_position,is_manual_player):
    print("Saving drafted player to database")

    current_auction_manager = get_object_or_404(auction_manager,pk=1)
    winning_team_object = get_object_or_404(auction_user,team_name=winning_team)

    if current_auction_manager.auction_type == 'rookie':
        winning_years_drafted = 1
        winning_bid = 1
        is_rookie_value = True
    else:
        winning_years_drafted = current_auction_manager.highest_contract_years
        winning_bid = current_auction_manager.highest_bid
        is_rookie_value = False
    
    print("Winning Bid: " + str(winning_bid))

    #save the rookie drafted
    drafted_player.objects.create(
        team=drafted_player_team,
        position=drafted_player_position,
        full_name=drafted_player_full_name,
        
        team_drafted_by=winning_team,
        years_drafted=winning_years_drafted,
        contract_price=winning_bid,
        is_rookie=is_rookie_value,
        is_manual=is_manual_player,
        draft_type=current_auction_manager.auction_type
    )

    #mark the drafted player in the player database
    try:
        drafted_player_nfl_player = get_object_or_404(nfl_player,full_name=drafted_player_full_name,position=drafted_player_position,team=drafted_player_team)
        drafted_player_nfl_player.drafted_by = str(winning_team_object.team_name)
        print("Updated Player Drafted By for: " + drafted_player_nfl_player.full_name)
        drafted_player_nfl_player.save()
    except:
        print("Unable to find player: " + drafted_player_full_name + ", " + drafted_player_team + ", " + drafted_player_position)

    
    #charge drafting team for rookie
    print("Math: " + str(int(winning_team_object.budget_remaining) - int(winning_bid)))
    winning_team_object.budget_remaining = int(int(winning_team_object.budget_remaining) - int(winning_bid))
    print("winning_team_object.budget_remaining: " + str(winning_team_object.budget_remaining))
    winning_team_object.save()
    
    winning_team_object = get_object_or_404(auction_user,team_name=winning_team)
    print("winning_team_object.budget_remaining: " + str(winning_team_object.budget_remaining))

def submit_auction_player(submitted_player_data):
    reset_auction_table()

    current_auction_manager = get_object_or_404(auction_manager,pk=1)

    if submitted_player_data['admin_bid_override']:
        source_auction_user = get_object_or_404(auction_user,draft_order=current_auction_manager.active_bidder)
    else:
        source_auction_user = get_object_or_404(auction_user,team_name=submitted_player_data['team_name'])

    current_auction_manager.player_for_auction_name = submitted_player_data['submitted_player_name']
    current_auction_manager.player_for_auction_team = submitted_player_data['submitted_player_team']
    current_auction_manager.player_for_auction_position = submitted_player_data['submitted_player_position']
    
    current_auction_manager.save()

    current_auction_manager = get_object_or_404(auction_manager,pk=1)

    #check to see if this player is manually entered
    nfl_player_check = nfl_player.objects.filter(full_name=current_auction_manager.player_for_auction_name,team=current_auction_manager.player_for_auction_team,position=current_auction_manager.player_for_auction_position)
    #print("nfl_player_check: " + str(nfl_player_check))
    if len(nfl_player_check) > 0:
        drafted_player_is_manual = False
    else:
        drafted_player_is_manual = True

    if current_auction_manager.auction_type == "rookie":
        
        save_drafted_player(source_auction_user.team_name,submitted_player_data['submitted_player_name'],submitted_player_data['submitted_player_team'],submitted_player_data['submitted_player_position'],drafted_player_is_manual)

        #for rookie auction, there is no bidding so move to the next person
        new_bid_start = get_next_bidder(current_auction_manager.active_bidder,current_auction_manager.initiated_auction,current_auction_manager.auction_type,True)

    else:
        #otherwise the user who selected them 
        new_bid_start = int(source_auction_user.draft_order)


    current_auction_manager = get_object_or_404(auction_manager,pk=1)

    current_auction_manager.active_bidder = new_bid_start
    current_auction_manager.initiated_auction = new_bid_start

    current_auction_manager.save()

    update_auction_table('all')

def start_new_auction_at_bidder(new_start_data,is_manual):
    reset_auction_table()

    current_auction_manager = get_object_or_404(auction_manager,pk=1)

    new_bid_start = int(new_start_data['new_bid_start'])
    current_auction_manager.auction_type = str(new_start_data['new_bid_type'])

    if str(new_start_data['new_bid_type']) == 'rookie' and is_manual == True:
        rookie_draft_order = current_auction_manager.rookie_draft_order
        #print("Rookie Draft order is: " + str(rookie_draft_order))
        
        #subtracting 1 here to convert to array start of 0
        next_rookie_draft_position = new_bid_start - 1
        

        if next_rookie_draft_position > (len(rookie_draft_order) - 1) or next_rookie_draft_position < 0:
            print("Invalid rookie index, setting to 0")
            new_bid_start = 0
        else:
            print("Returning Rookie Draft user: " + str(rookie_draft_order[next_rookie_draft_position]))
            
            current_auction_manager.rookie_draft_current_position = int(next_rookie_draft_position)

            new_bid_start = rookie_draft_order[next_rookie_draft_position]

    current_auction_manager.active_bidder = new_bid_start
    current_auction_manager.initiated_auction = new_bid_start
    current_auction_manager.auction_state = "bidding"

    current_auction_manager.highest_contract_years = 1
    current_auction_manager.highest_bid = 0

    current_auction_manager.player_for_auction_name = ""
    current_auction_manager.player_for_auction_team = ""
    current_auction_manager.player_for_auction_position = ""

    current_auction_manager.save()

    update_auction_table('all')

def reset_auction_table():
    all_auction_users = auction_user.objects.all()

    for a_user in all_auction_users:
        a_user.current_bid = 0
        a_user.contract_years_bid = 1
        a_user.pass_available = True
        a_user.still_in_auction = True
        a_user.save()

def reset_drop_outs():
    all_auction_users = auction_user.objects.all()

    for a_user in all_auction_users:
        a_user.dropped_out_of_selection = False
        a_user.save()

def reset_auction_manager():
    
    current_auction_manager = get_object_or_404(auction_manager,pk=1)
    current_auction_manager.highest_bid = 0
    current_auction_manager.active_bidder = 0
    current_auction_manager.highest_contract_years = 1
    current_auction_manager.initiated_auction = 0
    current_auction_manager.team_with_highest_bid = 0
    
    #current_auction_manager.rookie_draft_current_position = 0

    current_auction_manager.player_for_auction_name = ""
    current_auction_manager.player_for_auction_team = ""
    current_auction_manager.player_for_auction_position = ""

    current_auction_manager.save()

    update_auction_table('all')

def refresh_auction_table(refresh_target):
    print("Triggering Update of Auction Table")
    # dummy_instance = auction_manager(pk=1)
    # post_save.send(auction_manager, instance=dummy_instance)
    update_auction_table(refresh_target)

def send_ufa_auction_bidding_end(auction_winner,initiated_auction):
    print("UFA Auction is ending")

    current_auction_manager = get_object_or_404(auction_manager,pk=1) 
    current_auction_manager.auction_state = 'ufa_confirmation_request'
    current_auction_manager.save()

    winning_player_name = current_auction_manager.player_for_auction_name
    winning_contract_years = current_auction_manager.highest_contract_years
    winning_contract_cost = current_auction_manager.highest_bid
    
    channel_layer = channels.layers.get_channel_layer()
    group_name = settings.AUCTION_UPDATE_GROUP

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'auction_end_confirmation',
            'confirmation_step': 'ufa_confirmation_request',
            'auction_winner':auction_winner,
            'initiated_auction':initiated_auction,
            'winning_player_name':winning_player_name,
            'winning_contract_years':winning_contract_years,
            'winning_contract_cost':winning_contract_cost
        }
    )

def ufa_auction_end_confirmed(winner_confirm_reject):
    print("UFA Auction has ended: " + winner_confirm_reject)

def send_rfa_auction_bidding_end(bid_winner,initiated_auction):
    print("RFA Auction bidding is ending")

    current_auction_manager = get_object_or_404(auction_manager,pk=1) 
    current_auction_manager.auction_state = 'rfa_owner_match_request_1'
    current_auction_manager.save()

    channel_layer = channels.layers.get_channel_layer()
    group_name = settings.AUCTION_UPDATE_GROUP

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'auction_end_confirmation',
            'confirmation_step': 'rfa_owner_match_request_1',
            'auction_winner':bid_winner,
            'initiated_auction':initiated_auction,
            'winning_player_name':None,
            'winning_contract_years':None,
            'winning_contract_cost':None
        }
    )

def submit_new_bid(new_bid_data):
    all_auction_users = auction_user.objects.all()
    current_auction_manager = get_object_or_404(auction_manager,pk=1)

    if new_bid_data['admin_bid_override']:
        source_auction_user = get_object_or_404(auction_user,draft_order=current_auction_manager.active_bidder)
    else:
        source_auction_user = get_object_or_404(auction_user,team_name=new_bid_data['team_name'])

    if current_auction_manager.active_bidder == source_auction_user.draft_order or new_bid_data['admin_bid_override']:
                
                # if the bid contract years is greater highest bid contract years
        if (    ( int(new_bid_data['new_bid_contract_years']) >= current_auction_manager.highest_contract_years) and 
                    # if the new bid is higher than highest bid
                (   (int(new_bid_data['new_bid']) > current_auction_manager.highest_bid) or 
                    # or we are starting a new rfa or ufa bid
                    ( (current_auction_manager.auction_type == "rfa" or current_auction_manager.auction_type == "ufa") and int(new_bid_data['new_bid']) == 0)
                ) 
        ):

            source_auction_user.current_bid = new_bid_data['new_bid']
            source_auction_user.contract_years_bid = new_bid_data['new_bid_contract_years']
            source_auction_user.save()
            
            current_auction_manager.highest_bid = new_bid_data['new_bid']
            current_auction_manager.highest_contract_years = new_bid_data['new_bid_contract_years']
            current_auction_manager.team_with_highest_bid = source_auction_user.draft_order
            
            current_auction_manager.save()

            next_bidder_draft_order = get_next_bidder(current_auction_manager.active_bidder,current_auction_manager.initiated_auction,current_auction_manager.auction_type,False)
            print("Next Bidder: " + str(next_bidder_draft_order))
            
            current_auction_manager.active_bidder = next_bidder_draft_order
            current_auction_manager.save()

            update_auction_table('all')

        else:
            print("New bid less than highest bid")
    else:
        print("Current user can not bid, it is not their turn")

def pass_user(pass_data):
    all_auction_users = auction_user.objects.all()
    current_auction_manager = get_object_or_404(auction_manager,pk=1)

    if pass_data['admin_bid_override']:
        source_auction_user = get_object_or_404(auction_user,draft_order=current_auction_manager.active_bidder)
    else:
        source_auction_user = get_object_or_404(auction_user,team_name=pass_data['team_name'])
    
    #check how many teams remaining, if only 2 or 3, do not allow pass
    num_teams_remaining = 0
    for user in all_auction_users:
        if user.still_in_auction == True:
            num_teams_remaining += 1

    print("Teams Remaining: " + str(num_teams_remaining))
    #for rfa, 3 teams remaining really only means 2 bidding if you include the rfa owner, for ufa only 2 remaining
    if (current_auction_manager.auction_type == 'rfa' and num_teams_remaining == 3) or (current_auction_manager.auction_type == 'ufa' and num_teams_remaining == 2):
        print("Only 2 teams remaining, user can not pass")
        return


    if current_auction_manager.active_bidder == source_auction_user.draft_order:
        if source_auction_user.pass_available == True:
            source_auction_user.pass_available = False
            source_auction_user.save()

            next_bidder_draft_order = get_next_bidder(current_auction_manager.active_bidder,current_auction_manager.initiated_auction,current_auction_manager.auction_type,False)
            print("Next Bidder: " + str(next_bidder_draft_order))
            current_auction_manager.active_bidder = next_bidder_draft_order
            current_auction_manager.save()

            update_auction_table('all')

        else:
            print("Current user has no pass available")
    else:
        print("Current user can not pass, it is not their turn")

def drop_out_user(drop_out_data):
    all_auction_users = auction_user.objects.all()
    current_auction_manager = get_object_or_404(auction_manager,pk=1)

    if drop_out_data['admin_bid_override']:
        source_auction_user = get_object_or_404(auction_user,draft_order=current_auction_manager.active_bidder)
    else:
        source_auction_user = get_object_or_404(auction_user,team_name=drop_out_data['team_name'])

    if current_auction_manager.active_bidder == source_auction_user.draft_order:
        if source_auction_user.still_in_auction == True:
            source_auction_user.still_in_auction = False
            source_auction_user.save()

            next_bidder_draft_order = get_next_bidder(current_auction_manager.active_bidder,current_auction_manager.initiated_auction,current_auction_manager.auction_type,False)
            print("Next Bidder: " + str(next_bidder_draft_order))
            current_auction_manager.active_bidder = next_bidder_draft_order
            current_auction_manager.save()

            update_auction_table('all')

            auction_users_still_in = auction_user.objects.filter(still_in_auction=True,bathroom_mode_enabled=False) #only filter all user still in and not in bathroom mode
            num_auction_users_still_in = auction_user.objects.filter(still_in_auction=True,bathroom_mode_enabled=False).count() #only filter all user still in and not in bathroom mode
            if current_auction_manager.auction_type == "rfa" and num_auction_users_still_in == 2:
                print("Auction is RFA and only 2 auction users left")
                #need to determine which of the two users is the original owner
                #if first index has the same draft order as initiated auction, must be other
                if (auction_users_still_in[0].draft_order == current_auction_manager.initiated_auction):
                    bid_winner = auction_users_still_in[1].team_name
                else:
                    #if 0 not the same as initiated auction, must be 0
                    bid_winner = auction_users_still_in[0].team_name
                
                send_rfa_auction_bidding_end(bid_winner,get_object_or_404(auction_user,draft_order=current_auction_manager.initiated_auction).team_name)
            elif current_auction_manager.auction_type == "ufa" and num_auction_users_still_in == 1:
                print("Auction is UFA and only 1 auction users left")
                send_ufa_auction_bidding_end(auction_users_still_in[0].team_name,get_object_or_404(auction_user,draft_order=current_auction_manager.initiated_auction).team_name )
        else:
            print("Current user already dropped out")
    else:
        print("Current user can not pass, it is not their turn")

def get_next_bidder(active_bidder_draft_order,initiated_auction_draft_order,auction_type,is_player_selection):
    all_auction_users = auction_user.objects.all().order_by('draft_order')
    print("all_auction_users.count: " + str(all_auction_users.count()))
    print(str(list(range(active_bidder_draft_order,all_auction_users.count()))))
    print(str(list(range(0,active_bidder_draft_order -1))))
    all_auction_users_order = list(range(active_bidder_draft_order,all_auction_users.count())) + list(range(0,active_bidder_draft_order -1) )
    print("all_auction_users_order: " + str(all_auction_users_order))
    if is_player_selection == True: 
        #if this is player selection, we can go again, but only if everyone else cant
        #therefore we need to add ourselves to the list
        all_auction_users_order.append(int(active_bidder_draft_order-1))
        print("Updated users ordered for player selection: " + str(all_auction_users_order))
    
    all_auction_users_ordered = [all_auction_users[i] for i in all_auction_users_order]

    current_auction_manager = get_object_or_404(auction_manager,pk=1)


    if auction_type == 'rookie':
        rookie_draft_order = current_auction_manager.rookie_draft_order
        #print("Rookie Draft order is: " + str(rookie_draft_order))
        
        rookie_draft_current_position = current_auction_manager.rookie_draft_current_position
        #print("Current Rookie Draft posotion is: " + str(rookie_draft_current_position))
        
        next_rookie_draft_position = rookie_draft_current_position + 1
        print("Next Rookie Draft position is: " + str(next_rookie_draft_position))

        if next_rookie_draft_position > (len(rookie_draft_order) - 1):
            print("Rookie Draft is over!")
            return 0
        else:
            print("Returning Rookie Draft user: " + str(rookie_draft_order[next_rookie_draft_position]))
            
            current_auction_manager.rookie_draft_current_position = int(next_rookie_draft_position)
            current_auction_manager.save()

            return rookie_draft_order[next_rookie_draft_position]

    if is_player_selection == True: 

        #if this is initial player selection, follow player selection criteria for next user
        for a_user in all_auction_users_ordered:
            print("")
            print("Check draft order: " + str(a_user.draft_order))
            print("Check dropped out of selection: " + str(a_user.dropped_out_of_selection))
            #print("Current user did not initiate the current auction: " + str(a_user.draft_order != initiated_auction_draft_order))

            if  ( 
                    (a_user.dropped_out_of_selection == False) and              #we must not have dropped out of selection
                    (a_user.bathroom_mode_enabled == False)                     #we are not in bathroom mode
                    #(a_user.draft_order != initiated_auction_draft_order) and  #we are not the one who initiated the current auction
                ): 
                    if (current_auction_manager.auction_type == 'rfa' and len(a_user.current_rfa_list) == 0):    #if rfa we must have rfas left
                        print("Skipping because rfa and has no more rfas left")
                        continue

                    print("Next team: " + str(a_user.draft_order) )
                    return a_user.draft_order
    
    else:     
        #otherwise this must be bidding and follow bidding criteria
        for a_user in all_auction_users_ordered:
            print("")
            print("Check draft order: " + str(a_user.draft_order))
            print("Check active bidder draft order: " + str(active_bidder_draft_order))
            print("Check still in: " + str(a_user.still_in_auction))
            print("Current user is not active bidder: " + str(a_user.draft_order != active_bidder_draft_order))
            print("Bid Type is RFA and initiated draft: " + str((auction_type == 'rfa') and (a_user.draft_order == initiated_auction_draft_order)))
            print("a_user.draft_order: " + str(a_user.draft_order))
            print("current_auction_manager.team_with_highest_bid: " + str(current_auction_manager.team_with_highest_bid))
            print("Current user did not made the highest bid: " + str(a_user.draft_order != current_auction_manager.team_with_highest_bid))

            if  (   
                    (a_user.still_in_auction == True) and #we must still be in the auction
                    (a_user.draft_order != active_bidder_draft_order) and #we are not the one who submitted the latest bid
                    not ( (auction_type == 'rfa') and (a_user.draft_order == initiated_auction_draft_order) ) and #in RFA bidding the user who initiated does not bid until the end
                    (a_user.bathroom_mode_enabled == False) and #we are not in bathroom mode
                    ( (a_user.draft_order != current_auction_manager.team_with_highest_bid) ) #make sure we didnt make the highest bid
                ): 
                
                print("Next team: " + str(a_user.draft_order) )
                return a_user.draft_order
    
    
    #didnt find any viable next bidders/initiator so draft must be over
    print("No vible next team found...")
    return 0

def get_player_search_results(player_search_text_data):
    #print("Search Text: " + str(player_search_text_data['player_search_text']))
    #print("Search Team: " + str(player_search_text_data['searching_team']))

    #if search string is empty, clear results
    if player_search_text_data['player_search_text'] == "":
        first_5_players_from_search_s = serializers.serialize('json', [])
    else:
        first_5_players_from_search_undrafted = nfl_player.objects.filter(full_name__icontains=str(player_search_text_data['player_search_text']),drafted_by='Undrafted')[:5]
        first_5_players_from_search_drafted = nfl_player.objects.filter(full_name__icontains=str(player_search_text_data['player_search_text'])).exclude(drafted_by='Undrafted')[:5]
        first_5_players_from_search_final = list(chain(first_5_players_from_search_undrafted,first_5_players_from_search_drafted))[:5]

        first_5_players_from_search_s = serializers.serialize('json', first_5_players_from_search_final)

    # for player in first_5_players_from_search:
    #     print("Player Name: " + player.full_name)
    
    channel_layer = channels.layers.get_channel_layer()
    group_name = settings.PLAYER_SEARCH_GROUP

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'player_search_results',
            'search_result_data': first_5_players_from_search_s,
            'searching_team': str(player_search_text_data['searching_team'])
        }
    )
    