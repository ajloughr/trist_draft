import pytest
import json
from unittest.mock import patch
from trist_draft.apps.auction_table.models import auction_user, auction_manager, nfl_player
from trist_draft.apps.auction_table.consumers import update_auction_table

pytestmark = pytest.mark.django_db


def test_auction_table_view_roster_context(client, ten_team_league, dummy_player):
    """Test auction_table_view passes rostered_players in context."""
    user = ten_team_league['users'][0].user
    dummy_player.drafted_by = ten_team_league['users'][0].team_name
    dummy_player.save()

    client.force_login(user)
    response = client.get('/auction/')
    assert response.status_code == 200
    assert 'rostered_players' in response.context
    rostered = response.context['rostered_players']
    assert dummy_player in rostered


@patch('trist_draft.apps.auction_table.consumers.async_to_sync')
def test_update_auction_table_includes_rostered_players(mock_async_to_sync, ten_team_league, dummy_player):
    """Test update_auction_table broadcasts all_rostered_players_data."""
    dummy_player.drafted_by = ten_team_league['users'][0].team_name
    dummy_player.save()

    update_auction_table('all')

    assert mock_async_to_sync.called
    call_args = mock_async_to_sync.return_value.call_args[0]
    payload = call_args[1]

    assert 'all_rostered_players_data' in payload
    rostered_data = json.loads(payload['all_rostered_players_data'])
    assert len(rostered_data) > 0
    assert rostered_data[0]['fields']['full_name'] == dummy_player.full_name
    assert rostered_data[0]['fields']['drafted_by'] == ten_team_league['users'][0].team_name
