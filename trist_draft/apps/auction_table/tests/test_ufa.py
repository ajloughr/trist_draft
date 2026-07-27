import pytest
from unittest.mock import patch
from django.shortcuts import get_object_or_404

from trist_draft.apps.auction_table.models import auction_user, auction_manager, drafted_player

pytestmark = pytest.mark.django_db

@patch('trist_draft.apps.auction_table.consumers.send_ufa_auction_bidding_end')
def test_ufa_nomination_and_win(mock_send_bidding_end, ten_team_league, dummy_player):
    """
    Test Workflow C: UFA Bidding and Win
    Team 1 nominates a UFA with initial $1 bid.
    Team 2 bids $10. Teams 3-10 drop out.
    Team 1 drops out. Team 2 wins.
    """
    from trist_draft.apps.auction_table.consumers import submit_auction_player, submit_new_bid, drop_out_user
    
    manager = ten_team_league['manager']
    manager.auction_type = "ufa"
    manager.active_bidder = 1
    manager.initiated_auction = 1
    manager.save()
    
    users = ten_team_league['users']
    team_1 = users[0]
    team_2 = users[1]
    
    submit_auction_player({
        'admin_bid_override': False,
        'team_name': team_1.team_name,
        'submitted_player_name': dummy_player.full_name,
        'submitted_player_team': dummy_player.team,
        'submitted_player_position': dummy_player.position
    })
    
    submit_new_bid({
        'admin_bid_override': False,
        'team_name': team_1.team_name,
        'new_bid': 1,
        'new_bid_contract_years': 1
    })
    
    submit_new_bid({
        'admin_bid_override': False,
        'team_name': team_2.team_name,
        'new_bid': 10,
        'new_bid_contract_years': 1
    })
    
    for user in users[2:]:
        drop_out_user({
            'admin_bid_override': False,
            'team_name': user.team_name
        })
        
    drop_out_user({
        'admin_bid_override': False,
        'team_name': team_1.team_name
    })
    
    mock_send_bidding_end.assert_called_once_with(team_2.team_name, team_1.team_name)

@patch('trist_draft.apps.auction_table.consumers.send_ufa_auction_bidding_end')
def test_ufa_uncontested_nomination(mock_send_bidding_end, ten_team_league, dummy_player):
    from trist_draft.apps.auction_table.consumers import submit_auction_player, submit_new_bid, drop_out_user
    manager = ten_team_league['manager']
    manager.auction_type = "ufa"
    manager.active_bidder = 1
    manager.initiated_auction = 1
    manager.save()
    
    users = ten_team_league['users']
    team_1 = users[0]
    
    submit_auction_player({
        'admin_bid_override': False,
        'team_name': team_1.team_name,
        'submitted_player_name': dummy_player.full_name,
        'submitted_player_team': dummy_player.team,
        'submitted_player_position': dummy_player.position
    })
    
    submit_new_bid({
        'admin_bid_override': False,
        'team_name': team_1.team_name,
        'new_bid': 1,
        'new_bid_contract_years': 1
    })
    
    for user in users[1:]:
        drop_out_user({
            'admin_bid_override': False,
            'team_name': user.team_name
        })
        
    mock_send_bidding_end.assert_called_once_with(team_1.team_name, team_1.team_name)

@patch('trist_draft.apps.auction_table.consumers.send_ufa_auction_bidding_end')
def test_ufa_extended_bidding_war(mock_send_bidding_end, ten_team_league, dummy_player):
    from trist_draft.apps.auction_table.consumers import submit_auction_player, submit_new_bid, drop_out_user
    manager = ten_team_league['manager']
    manager.auction_type = "ufa"
    manager.active_bidder = 1
    manager.initiated_auction = 1
    manager.save()
    
    users = ten_team_league['users']
    team_1 = users[0]
    team_2 = users[1]
    team_3 = users[2]
    
    submit_auction_player({
        'admin_bid_override': False,
        'team_name': team_1.team_name,
        'submitted_player_name': dummy_player.full_name,
        'submitted_player_team': dummy_player.team,
        'submitted_player_position': dummy_player.position
    })
    submit_new_bid({'admin_bid_override': False, 'team_name': team_1.team_name, 'new_bid': 1, 'new_bid_contract_years': 1})
    
    # War begins
    submit_new_bid({'admin_bid_override': False, 'team_name': team_2.team_name, 'new_bid': 2, 'new_bid_contract_years': 1})
    submit_new_bid({'admin_bid_override': False, 'team_name': team_3.team_name, 'new_bid': 3, 'new_bid_contract_years': 1})
    
    # Teams 4-10 drop out
    for user in users[3:]:
        drop_out_user({'admin_bid_override': False, 'team_name': user.team_name})
        
    # Back to team 1, drops out
    drop_out_user({'admin_bid_override': False, 'team_name': team_1.team_name})
    
    # Team 2 raises again
    submit_new_bid({'admin_bid_override': False, 'team_name': team_2.team_name, 'new_bid': 4, 'new_bid_contract_years': 1})
    
    # Team 3 drops out
    drop_out_user({'admin_bid_override': False, 'team_name': team_3.team_name})
    
    mock_send_bidding_end.assert_called_once_with(team_2.team_name, team_1.team_name)

def test_ufa_dropping_out_of_player_selection(ten_team_league):
    from trist_draft.apps.auction_table.consumers import drop_out_of_or_pass_player_selection
    manager = ten_team_league['manager']
    manager.auction_type = "ufa"
    manager.active_bidder = 1
    manager.initiated_auction = 1
    manager.save()
    
    users = ten_team_league['users']
    team_1 = users[0]
    
    drop_out_of_or_pass_player_selection({
        'admin_bid_override': False,
        'team_name': team_1.team_name
    }, is_drop_out=True)
    
    manager.refresh_from_db()
    assert manager.active_bidder == 2
    assert manager.initiated_auction == 2

@patch('trist_draft.apps.auction_table.consumers.send_ufa_auction_bidding_end')
def test_ufa_auto_pass_early_bid_dropout(mock_send_bidding_end, ten_team_league, dummy_player):
    from trist_draft.apps.auction_table.consumers import submit_auction_player, submit_new_bid
    manager = ten_team_league['manager']
    manager.auction_type = "ufa"
    manager.active_bidder = 1
    manager.initiated_auction = 1
    manager.save()
    
    users = ten_team_league['users']
    team_1 = users[0]
    team_2 = users[1]
    team_3 = users[2]
    
    submit_auction_player({
        'admin_bid_override': False,
        'team_name': team_1.team_name,
        'submitted_player_name': dummy_player.full_name,
        'submitted_player_team': dummy_player.team,
        'submitted_player_position': dummy_player.position
    })
    
    # Team 3 turns on auto pass early (must be done after player is submitted because submit resets this field)
    team_3.dropped_out_of_bid_early = True
    team_3.save()
    
    submit_new_bid({'admin_bid_override': False, 'team_name': team_1.team_name, 'new_bid': 1, 'new_bid_contract_years': 1})
    
    submit_new_bid({'admin_bid_override': False, 'team_name': team_2.team_name, 'new_bid': 2, 'new_bid_contract_years': 1})
    
    manager.refresh_from_db()
    assert manager.active_bidder == 4

def test_ufa_all_teams_drop_out_of_player_selection(ten_team_league):
    from trist_draft.apps.auction_table.consumers import drop_out_of_or_pass_player_selection
    manager = ten_team_league['manager']
    manager.auction_type = "ufa"
    manager.active_bidder = 1
    manager.initiated_auction = 1
    manager.save()
    
    users = ten_team_league['users']
    
    # All 10 teams drop out
    for user in users:
        drop_out_of_or_pass_player_selection({
            'admin_bid_override': False,
            'team_name': user.team_name
        }, is_drop_out=True)
        
    manager.refresh_from_db()
    # When all users drop out, active_bidder should be set to 0 to indicate the draft is over
    assert manager.active_bidder == 0

@patch('trist_draft.apps.auction_table.consumers.send_ufa_auction_bidding_end')
def test_ufa_admin_bid_override(mock_send_bidding_end, ten_team_league, dummy_player):
    from trist_draft.apps.auction_table.consumers import submit_auction_player, submit_new_bid
    manager = ten_team_league['manager']
    manager.auction_type = "ufa"
    manager.active_bidder = 1
    manager.initiated_auction = 1
    manager.save()
    
    users = ten_team_league['users']
    team_1 = users[0]
    team_3 = users[2]
    
    submit_auction_player({
        'admin_bid_override': False,
        'team_name': team_1.team_name,
        'submitted_player_name': dummy_player.full_name,
        'submitted_player_team': dummy_player.team,
        'submitted_player_position': dummy_player.position
    })
    
    submit_new_bid({
        'admin_bid_override': False,
        'team_name': team_1.team_name,
        'new_bid': 1,
        'new_bid_contract_years': 1
    })
    
    # Admin manually places a bid for team 3 when it's team 2's turn
    # Since admin_bid_override applies to the active bidder (team 2), it acts on behalf of team 2.
    submit_new_bid({
        'admin_bid_override': True, # Admin Override
        'team_name': team_3.team_name, # This is ignored because of admin override
        'new_bid': 50,
        'new_bid_contract_years': 1
    })
    
    manager.refresh_from_db()
    assert manager.team_with_highest_bid == 2
    assert manager.highest_bid == 50
    # Next turn should be team 3.
    assert manager.active_bidder == 3

@patch('trist_draft.apps.auction_table.consumers.send_ufa_auction_bidding_end')
def test_ufa_bathroom_mode_auto_forfeit(mock_send_bidding_end, ten_team_league, dummy_player):
    from trist_draft.apps.auction_table.consumers import submit_auction_player, submit_new_bid, toggle_bathroom_mode, drop_out_user
    manager = ten_team_league['manager']
    manager.auction_type = "ufa"
    manager.active_bidder = 1
    manager.initiated_auction = 1
    manager.save()
    
    users = ten_team_league['users']
    team_1 = users[0]
    team_2 = users[1]
    team_3 = users[2]
    
    submit_auction_player({
        'admin_bid_override': False,
        'team_name': team_1.team_name,
        'submitted_player_name': dummy_player.full_name,
        'submitted_player_team': dummy_player.team,
        'submitted_player_position': dummy_player.position
    })
    submit_new_bid({'admin_bid_override': False, 'team_name': team_1.team_name, 'new_bid': 1, 'new_bid_contract_years': 1})
    
    # Teams 4-10 drop out
    for user in users[3:]:
        drop_out_user({'admin_bid_override': False, 'team_name': user.team_name})
        
    # Team 2 and 3 war
    submit_new_bid({'admin_bid_override': False, 'team_name': team_2.team_name, 'new_bid': 2, 'new_bid_contract_years': 1})
    submit_new_bid({'admin_bid_override': False, 'team_name': team_3.team_name, 'new_bid': 3, 'new_bid_contract_years': 1})
    
    # Team 1 drops out
    drop_out_user({'admin_bid_override': False, 'team_name': team_1.team_name})
    
    # Team 2 raises to 4
    submit_new_bid({'admin_bid_override': False, 'team_name': team_2.team_name, 'new_bid': 4, 'new_bid_contract_years': 1})
    
    # Now it is Team 3's turn, but Team 3 goes to the bathroom!
    toggle_bathroom_mode(team_3.team_name, True)
    drop_out_user({'admin_bid_override': False, 'team_name': team_3.team_name})
    
    mock_send_bidding_end.assert_called_once_with(team_2.team_name, team_1.team_name)

def test_ufa_bathroom_mode_skip_nomination(ten_team_league):
    from trist_draft.apps.auction_table.consumers import drop_out_of_or_pass_player_selection, toggle_bathroom_mode
    manager = ten_team_league['manager']
    manager.auction_type = "ufa"
    manager.active_bidder = 1
    manager.initiated_auction = 1
    manager.save()
    
    users = ten_team_league['users']
    team_1 = users[0]
    team_2 = users[1]
    team_3 = users[2]
    
    # Team 2 is in the bathroom
    toggle_bathroom_mode(team_2.team_name, True)
    
    # Team 1 drops out of player selection (simulating their turn ending)
    drop_out_of_or_pass_player_selection({
        'admin_bid_override': False,
        'team_name': team_1.team_name
    }, is_drop_out=True)
    
    manager.refresh_from_db()
    # Team 2 is in the bathroom, so it should skip them and go to Team 3
    assert manager.active_bidder == 3
    assert manager.initiated_auction == 3

@patch('trist_draft.apps.auction_table.consumers.send_ufa_auction_bidding_end')
def test_ufa_complex_bidding_sequence(mock_send_bidding_end, ten_team_league, dummy_player):
    """
    Simulates a very chaotic bidding sequence with 20+ bids across multiple loops.
    Teams drop out slowly. Intermediate assertions check the exact state of active_bidder.
    """
    from trist_draft.apps.auction_table.consumers import submit_auction_player, submit_new_bid, drop_out_user
    manager = ten_team_league['manager']
    manager.auction_type = "ufa"
    manager.active_bidder = 1
    manager.initiated_auction = 1
    manager.save()
    
    users = ten_team_league['users']
    t1, t2, t3, t4, t5, t6, t7, t8, t9, t10 = [u.team_name for u in users]
    
    # Team 1 Nominates
    submit_auction_player({
        'admin_bid_override': False,
        'team_name': t1,
        'submitted_player_name': dummy_player.full_name,
        'submitted_player_team': dummy_player.team,
        'submitted_player_position': dummy_player.position
    })
    
    # --- ROUND 1 ---
    submit_new_bid({'admin_bid_override': False, 'team_name': t1, 'new_bid': 1, 'new_bid_contract_years': 1})
    submit_new_bid({'admin_bid_override': False, 'team_name': t2, 'new_bid': 2, 'new_bid_contract_years': 1})
    submit_new_bid({'admin_bid_override': False, 'team_name': t3, 'new_bid': 3, 'new_bid_contract_years': 1})
    drop_out_user({'admin_bid_override': False, 'team_name': t4}) # Team 4 drops
    submit_new_bid({'admin_bid_override': False, 'team_name': t5, 'new_bid': 4, 'new_bid_contract_years': 1})
    submit_new_bid({'admin_bid_override': False, 'team_name': t6, 'new_bid': 5, 'new_bid_contract_years': 1})
    drop_out_user({'admin_bid_override': False, 'team_name': t7}) # Team 7 drops
    submit_new_bid({'admin_bid_override': False, 'team_name': t8, 'new_bid': 6, 'new_bid_contract_years': 1})
    submit_new_bid({'admin_bid_override': False, 'team_name': t9, 'new_bid': 7, 'new_bid_contract_years': 1})
    submit_new_bid({'admin_bid_override': False, 'team_name': t10, 'new_bid': 8, 'new_bid_contract_years': 1})
    
    # Verify State after Round 1
    manager.refresh_from_db()
    assert manager.highest_bid == 8
    assert manager.team_with_highest_bid == 10
    assert manager.active_bidder == 1 # Loop back to t1
    
    # --- ROUND 2 ---
    submit_new_bid({'admin_bid_override': False, 'team_name': t1, 'new_bid': 9, 'new_bid_contract_years': 1})
    drop_out_user({'admin_bid_override': False, 'team_name': t2}) # Team 2 drops
    submit_new_bid({'admin_bid_override': False, 'team_name': t3, 'new_bid': 10, 'new_bid_contract_years': 1})
    # t4 is already out, should automatically skip to t5
    manager.refresh_from_db()
    assert manager.active_bidder == 5
    
    drop_out_user({'admin_bid_override': False, 'team_name': t5}) # Team 5 drops
    submit_new_bid({'admin_bid_override': False, 'team_name': t6, 'new_bid': 11, 'new_bid_contract_years': 1})
    # t7 is already out, skips to t8
    submit_new_bid({'admin_bid_override': False, 'team_name': t8, 'new_bid': 12, 'new_bid_contract_years': 1})
    submit_new_bid({'admin_bid_override': False, 'team_name': t9, 'new_bid': 13, 'new_bid_contract_years': 1})
    drop_out_user({'admin_bid_override': False, 'team_name': t10}) # Team 10 drops
    
    # Verify State after Round 2
    manager.refresh_from_db()
    assert manager.highest_bid == 13
    assert manager.team_with_highest_bid == 9
    assert manager.active_bidder == 1 # Skips t10 back to t1
    
    # --- ROUND 3 (Only t1, t3, t6, t8, t9 remain) ---
    drop_out_user({'admin_bid_override': False, 'team_name': t1})
    submit_new_bid({'admin_bid_override': False, 'team_name': t3, 'new_bid': 15, 'new_bid_contract_years': 1})
    submit_new_bid({'admin_bid_override': False, 'team_name': t6, 'new_bid': 16, 'new_bid_contract_years': 1})
    submit_new_bid({'admin_bid_override': False, 'team_name': t8, 'new_bid': 20, 'new_bid_contract_years': 1})
    drop_out_user({'admin_bid_override': False, 'team_name': t9})
    
    # --- ROUND 4 (Only t3, t6, t8 remain, highest is t8 with 20) ---
    manager.refresh_from_db()
    assert manager.active_bidder == 3 # Skips back to t3
    
    submit_new_bid({'admin_bid_override': False, 'team_name': t3, 'new_bid': 22, 'new_bid_contract_years': 1})
    drop_out_user({'admin_bid_override': False, 'team_name': t6})
    submit_new_bid({'admin_bid_override': False, 'team_name': t8, 'new_bid': 25, 'new_bid_contract_years': 1})
    
    # --- ROUND 5 (Only t3, t8 remain) ---
    submit_new_bid({'admin_bid_override': False, 'team_name': t3, 'new_bid': 30, 'new_bid_contract_years': 1})
    drop_out_user({'admin_bid_override': False, 'team_name': t8}) # t8 finally drops out
    
    # The moment t8 drops out, t3 is the last team standing!
    # Assert that the auction ended exactly when t8 dropped out.
    mock_send_bidding_end.assert_called_once_with(t3, t1) # t3 wins, t1 nominated
    
    manager.refresh_from_db()
    assert manager.highest_bid == 30
    assert manager.team_with_highest_bid == 3
