from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
import uuid

class auction_user(models.Model):
    team_name                   = models.CharField(max_length=50)
    initiated_auction           = models.BooleanField(default=False)
    still_in_auction            = models.BooleanField(default=False)
    current_bid                 = models.IntegerField(blank=True, null=True, default=0)
    contract_years_bid          = models.IntegerField(blank=True, null=True, default=0)
    user                        = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user", default=0 )
    draft_order                 = models.IntegerField(default=999)
    currently_bidding           = models.BooleanField(default=False)
    last_bid_uuid               = models.UUIDField(default=uuid.uuid4, editable=False)
    pass_available              = models.BooleanField(default=True)
    dropped_out_of_selection    = models.BooleanField(default=False)
    bathroom_mode_enabled       = models.BooleanField(default=False)
    dropped_out_of_bid_early    = models.BooleanField(default=False)
    

    current_roster_size         = models.IntegerField(default=0) 

    starting_budget     = models.IntegerField(default=0) 
    budget_remaining    = models.IntegerField(default=0)

    initial_rfa_list    = ArrayField( models.IntegerField(), blank=True, default=list )
    current_rfa_list    = ArrayField( models.IntegerField(), blank=True, default=list )
    rfas_remaining      = models.IntegerField(default=0)
    
    @property
    def get_current_rfa_players(self):
        if not self.current_rfa_list:
            return []
        return nfl_player.objects.filter(player_id__in=self.current_rfa_list)

    def __str__(self):
        return "{} : {} : {}".format(self.draft_order, self.team_name,self.user)


class auction_manager(models.Model):
    active_bidder                   = models.IntegerField(default=0)
    bid_timer                       = models.IntegerField(default=0)
    bid_timer_active                = models.BooleanField(default=False)
    highest_bid                     = models.IntegerField(default=0)
    highest_contract_years          = models.IntegerField(default=0)
    team_with_highest_bid           = models.IntegerField(default=0)
    initiated_auction               = models.IntegerField(default=0)
    initial_bid                     = models.IntegerField(default=0)
    initial_bid_years               = models.IntegerField(default=0)
    auction_is_rookie               = models.BooleanField(default=False)
    auction_is_rfa                  = models.BooleanField(default=False)
    auction_is_ufa                  = models.BooleanField(default=False)
    auction_state                   = models.CharField(max_length=100,blank=True, null=True)

    #this isnt going to be used
    #rookie_draft_order              = models.CharField(max_length=100,default="")
    rookie_draft_order              = ArrayField( models.IntegerField(), blank=True, default=list )
    rookie_draft_current_position   = models.IntegerField(default=0)

    player_for_auction_name         = models.CharField(max_length=50,blank=True, null=True)
    player_for_auction_team         = models.CharField(max_length=50,blank=True, null=True)
    player_for_auction_position     = models.CharField(max_length=50,blank=True, null=True)
    player_for_auction_bye          = models.IntegerField(blank=True, null=True)

    
    ROOKIE = 'rookie'
    RFA = "rfa"
    UFA = "ufa"
    auction_type_choices    = [
                                (ROOKIE, 'Rookie'),
                                (RFA, 'Restricted Free Agent'),
                                (UFA, 'Unrestricted Free Agent'),
                            ]
    auction_type = models.CharField(
        max_length=10,
        choices=auction_type_choices,
        default=ROOKIE,
    )

class nfl_player(models.Model):
    player_id = models.PositiveSmallIntegerField(default=0)  # This maps to 'Rank'
    team_short_name = models.CharField(max_length=3)  # This maps to 'team_short_name'
    team = models.CharField(max_length=50)  # This maps to 'team'
    position = models.CharField(max_length=5)  # This maps to 'POS'
    full_name = models.CharField(max_length=100)  # This maps to 'Player'
    bye = models.PositiveSmallIntegerField(blank=True, null=True)  # This maps to 'Bye'

    # Other fields from the dataset as PositiveSmallIntegerField
    salary = models.PositiveSmallIntegerField(blank=True, null=True)
    final_year = models.PositiveSmallIntegerField(blank=True, null=True)


    drafted_by          = models.CharField(max_length=50,default="Undrafted")

    def __str__(self):
        return "{} : {} : {} : {} : {}".format(self.player_id, self.full_name,self.team,self.position,self.drafted_by)

class drafted_player(models.Model):
    team                = models.CharField(max_length=50)
    position            = models.CharField(max_length=5)
    full_name           = models.CharField(max_length=100)

    team_drafted_by     = models.CharField(max_length=50,default="")
    years_drafted       = models.PositiveSmallIntegerField()
    contract_price      = models.PositiveSmallIntegerField()
    is_rookie           = models.BooleanField(default=False)
    is_manual           = models.BooleanField(default=False)
    draft_type          = models.CharField(max_length=50,default="")

    def __str__(self):
        return "{} : {} : {} : {}".format(self.full_name,self.team,self.position,self.team_drafted_by)



