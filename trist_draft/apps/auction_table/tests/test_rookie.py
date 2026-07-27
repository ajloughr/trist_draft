import pytest
from unittest.mock import patch
from django.shortcuts import get_object_or_404

from trist_draft.apps.auction_table.models import auction_user, auction_manager, drafted_player
from trist_draft.apps.auction_table.consumers import submit_auction_player

pytestmark = pytest.mark.django_db

@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
def test_selecting_a_rookie(mock_update, ten_team_league, dummy_player):
    """
    Test Workflow A: Selecting a Rookie
    When a team selects a rookie during the rookie draft phase, it should completely bypass
    bidding and immediately assign the player for $1 / 1 year, and then rotate to the next pick.
    """
    # Arrange
    manager = ten_team_league['manager']
    manager.auction_type = "rookie"
    # Create a 10-team rookie draft order (using team draft_order 1 to 10)
    manager.rookie_draft_order = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    manager.rookie_draft_current_position = 0
    manager.active_bidder = 1
    manager.save()
    
    users = ten_team_league['users']
    team_1 = users[0] # Draft order 1
    
    # Act: Team 1 (draft_order=1) submits a rookie player
    submitted_data = {
        'admin_bid_override': False,
        'team_name': team_1.team_name,
        'submitted_player_name': dummy_player.full_name,
        'submitted_player_team': dummy_player.team,
        'submitted_player_position': dummy_player.position
    }
    
    submit_auction_player(submitted_data)
    
    # Assert
    # 1. Player should be drafted and correctly assigned
    drafted = drafted_player.objects.filter(full_name=dummy_player.full_name).first()
    assert drafted is not None
    assert drafted.team_drafted_by == team_1.team_name
    assert drafted.contract_price == 1
    assert drafted.years_drafted == 1
    assert drafted.is_rookie is True
    
    # 2. Team 1's budget should be decremented by $1
    team_1.refresh_from_db()
    assert team_1.budget_remaining == team_1.starting_budget - 1
    
    # 3. Manager state should rotate to the next rookie bidder (draft_order=2)
    manager.refresh_from_db()
    assert manager.active_bidder == 2
    
    # 4. WebSocket broadcast should be fired to all clients
    mock_update.assert_called_once_with('all')

@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
def test_rookie_snake_draft(mock_update, ten_team_league):
    """
    Test a full 2-round snake rookie draft (1 to 10, then 10 to 1).
    Ensures that active_bidder safely navigates the array and ends cleanly.
    """
    from trist_draft.apps.auction_table.tests.factories import NflPlayerFactory
    
    manager = ten_team_league['manager']
    manager.auction_type = "rookie"
    snake_order = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    manager.rookie_draft_order = snake_order
    manager.rookie_draft_current_position = 0
    manager.active_bidder = snake_order[0]
    manager.save()
    
    users = ten_team_league['users']
    
    # Generate 20 rookies
    rookies = []
    for i in range(20):
        rookies.append(NflPlayerFactory(full_name=f"Snake Rookie {i}", drafted_by="Undrafted"))
        
    # Simulate draft
    for index, draft_pick_team_order in enumerate(snake_order):
        team_user = next(u for u in users if u.draft_order == draft_pick_team_order)
        rookie_to_draft = rookies[index]
        
        submitted_data = {
            'admin_bid_override': False,
            'team_name': team_user.team_name,
            'submitted_player_name': rookie_to_draft.full_name,
            'submitted_player_team': rookie_to_draft.team,
            'submitted_player_position': rookie_to_draft.position
        }
        
        submit_auction_player(submitted_data)
        
        # Verify
        drafted = drafted_player.objects.filter(full_name=rookie_to_draft.full_name).first()
        assert drafted is not None
        assert drafted.team_drafted_by == team_user.team_name
        
        manager.refresh_from_db()
        if index < len(snake_order) - 1:
            expected_next_bidder = snake_order[index + 1]
            assert manager.active_bidder == expected_next_bidder
        else:
            # End of draft, should reset to 0
            assert manager.active_bidder == 0
            
    # Verify budgets (everyone should have spent $2)
    for u in users:
        u.refresh_from_db()
        assert u.budget_remaining == u.starting_budget - 2
