import factory
from django.contrib.auth.models import User
from trist_draft.apps.auction_table.models import auction_user, auction_manager, nfl_player, drafted_player

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user_{n}@example.com")

class AuctionUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = auction_user
    team_name = factory.Sequence(lambda n: f"Team {n}")
    user = factory.SubFactory(UserFactory)
    draft_order = factory.Sequence(lambda n: n)
    starting_budget = 100
    budget_remaining = 100
    pass_available = True
    still_in_auction = True

class AuctionManagerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = auction_manager
    active_bidder = 1
    initiated_auction = 1
    highest_bid = 0
    highest_contract_years = 1

class NflPlayerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = nfl_player
    player_id = factory.Sequence(lambda n: n)
    full_name = factory.Sequence(lambda n: f"Player {n}")
    team = "FA"
    position = "QB"
    drafted_by = "Undrafted"

class DraftedPlayerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = drafted_player
    full_name = factory.Sequence(lambda n: f"Drafted Player {n}")
    team = "FA"
    position = "QB"
    years_drafted = 1
    contract_price = 1
