import pytest
from .factories import UserFactory, AuctionUserFactory, AuctionManagerFactory, NflPlayerFactory
from unittest.mock import patch

@pytest.fixture
def ten_team_league(db):
    """Creates a standard 10-team league setup with an auction manager."""
    users = []
    for i in range(1, 11):
        users.append(AuctionUserFactory(draft_order=i, team_name=f"Team {i}"))
    
    manager = AuctionManagerFactory(
        pk=1, # pk=1 is hardcoded in consumers.py
        active_bidder=1,
        initiated_auction=1,
        auction_state="bidding",
        auction_type="ufa"
    )
    return {
        "users": users,
        "manager": manager
    }

@pytest.fixture
def dummy_player(db):
    return NflPlayerFactory(player_id=1, full_name="John Doe", position="QB", team="BUF")

@pytest.fixture(autouse=True)
def override_channel_layers(settings):
    """Override CHANNEL_LAYERS to use InMemoryChannelLayer to prevent Redis timeouts during tests."""
    settings.CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        }
    }
