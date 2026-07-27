import pytest
from unittest.mock import patch
from django.shortcuts import get_object_or_404

from trist_draft.apps.auction_table.models import auction_user, auction_manager, drafted_player
from trist_draft.apps.auction_table.consumers import submit_auction_player, submit_new_bid, drop_out_user, receive_auction_results_response, pass_user

pytestmark = pytest.mark.django_db

def _setup_rfa_auction(ten_team_league, dummy_player):
    """Helper to setup RFA auction base state."""
    manager = ten_team_league['manager']
    manager.auction_type = "rfa"
    manager.active_bidder = 1
    manager.initiated_auction = 1
    manager.save()
    
    users = ten_team_league['users']
    team_1 = users[0]
    
    # Give Team 1 the RFA dummy_player
    team_1.current_rfa_list = [str(dummy_player.player_id)]
    team_1.save()
    
    return manager, users, team_1

@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_bidding_end')
@patch('trist_draft.apps.auction_table.consumers.start_new_auction_at_bidder')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_end')
def test_rfa_owner_rejects_first_match(mock_send_end, mock_start_new, mock_send_bidding_end, mock_update, ten_team_league, dummy_player):
    """Scenario 1: Team 1 nominates -> Team 2 wins bidding -> Team 1 declines match -> Team 2 wins."""
    manager, users, team_1 = _setup_rfa_auction(ten_team_league, dummy_player)
    team_2 = users[1]
    
    submit_auction_player({'admin_bid_override': False, 'team_name': team_1.team_name, 'submitted_player_name': dummy_player.full_name, 'submitted_player_team': dummy_player.team, 'submitted_player_position': dummy_player.position})
    
    # Team 1 mandatory initial bid
    submit_new_bid({'admin_bid_override': False, 'team_name': team_1.team_name, 'new_bid': 1, 'new_bid_contract_years': 1})
    
    # Team 2 bids
    submit_new_bid({'admin_bid_override': False, 'team_name': team_2.team_name, 'new_bid': 5, 'new_bid_contract_years': 2})
    
    # Teams 3-10 drop out
    for user in users[2:]:
        drop_out_user({'admin_bid_override': False, 'team_name': user.team_name})
        
    # Match phase: Team 1 declines
    receive_auction_results_response({'results_response': 'rfa_owner_match_1_rejected'})
    
    # Assert Team 2 wins
    drafted = drafted_player.objects.filter(full_name=dummy_player.full_name).first()
    assert drafted.team_drafted_by == team_2.team_name
    assert drafted.contract_price == 5
    assert drafted.years_drafted == 2

@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_bidding_end')
@patch('trist_draft.apps.auction_table.consumers.start_new_auction_at_bidder')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_end')
def test_rfa_owner_matches_first_bidder_declines_raise(mock_send_end, mock_start_new, mock_send_bidding_end, mock_update, ten_team_league, dummy_player):
    """Scenario 2: Team 1 nominates -> Team 2 wins bidding -> Team 1 matches -> Team 2 declines raise -> Team 1 wins."""
    manager, users, team_1 = _setup_rfa_auction(ten_team_league, dummy_player)
    team_2 = users[1]
    
    submit_auction_player({'admin_bid_override': False, 'team_name': team_1.team_name, 'submitted_player_name': dummy_player.full_name, 'submitted_player_team': dummy_player.team, 'submitted_player_position': dummy_player.position})
    submit_new_bid({'admin_bid_override': False, 'team_name': team_1.team_name, 'new_bid': 1, 'new_bid_contract_years': 1})
    submit_new_bid({'admin_bid_override': False, 'team_name': team_2.team_name, 'new_bid': 5, 'new_bid_contract_years': 2})
    for user in users[2:]:
        drop_out_user({'admin_bid_override': False, 'team_name': user.team_name})
        
    # Match phase 1: Team 1 matches
    receive_auction_results_response({'results_response': 'rfa_owner_match_1_matched'})
    
    # Raise phase: Team 2 declines
    receive_auction_results_response({'results_response': 'rfa_bid_winner_dropped_out'})
    
    # Assert Team 1 wins at the matched price
    drafted = drafted_player.objects.filter(full_name=dummy_player.full_name).first()
    assert drafted.team_drafted_by == team_1.team_name
    assert drafted.contract_price == 5
    assert drafted.years_drafted == 2

@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_bidding_end')
@patch('trist_draft.apps.auction_table.consumers.start_new_auction_at_bidder')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_end')
def test_rfa_owner_matches_first_bidder_raises_owner_rejects(mock_send_end, mock_start_new, mock_send_bidding_end, mock_update, ten_team_league, dummy_player):
    """Scenario 3: Team 1 nominates -> Team 2 wins bidding -> Team 1 matches -> Team 2 raises -> Team 1 rejects -> Team 2 wins."""
    manager, users, team_1 = _setup_rfa_auction(ten_team_league, dummy_player)
    team_2 = users[1]
    
    submit_auction_player({'admin_bid_override': False, 'team_name': team_1.team_name, 'submitted_player_name': dummy_player.full_name, 'submitted_player_team': dummy_player.team, 'submitted_player_position': dummy_player.position})
    submit_new_bid({'admin_bid_override': False, 'team_name': team_1.team_name, 'new_bid': 1, 'new_bid_contract_years': 1})
    submit_new_bid({'admin_bid_override': False, 'team_name': team_2.team_name, 'new_bid': 5, 'new_bid_contract_years': 2})
    for user in users[2:]:
        drop_out_user({'admin_bid_override': False, 'team_name': user.team_name})
        
    # Match phase 1: Team 1 matches
    receive_auction_results_response({'results_response': 'rfa_owner_match_1_matched'})
    
    # Raise phase: Team 2 raises
    receive_auction_results_response({'results_response': 'rfa_bid_winner_raised', 'raise_bid': 7})
    
    # Match phase 2: Team 1 rejects
    receive_auction_results_response({'results_response': 'rfa_owner_match_2_rejected'})
    
    # Assert Team 2 wins at raised price
    drafted = drafted_player.objects.filter(full_name=dummy_player.full_name).first()
    assert drafted.team_drafted_by == team_2.team_name
    assert drafted.contract_price == 7
    assert drafted.years_drafted == 2

@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_bidding_end')
@patch('trist_draft.apps.auction_table.consumers.start_new_auction_at_bidder')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_end')
def test_rfa_owner_matches_first_bidder_raises_owner_matches_second(mock_send_end, mock_start_new, mock_send_bidding_end, mock_update, ten_team_league, dummy_player):
    """Scenario 4: Team 1 nominates -> Team 2 wins -> Team 1 matches -> Team 2 raises -> Team 1 matches -> Team 1 wins."""
    manager, users, team_1 = _setup_rfa_auction(ten_team_league, dummy_player)
    team_2 = users[1]
    
    submit_auction_player({'admin_bid_override': False, 'team_name': team_1.team_name, 'submitted_player_name': dummy_player.full_name, 'submitted_player_team': dummy_player.team, 'submitted_player_position': dummy_player.position})
    submit_new_bid({'admin_bid_override': False, 'team_name': team_1.team_name, 'new_bid': 1, 'new_bid_contract_years': 1})
    submit_new_bid({'admin_bid_override': False, 'team_name': team_2.team_name, 'new_bid': 5, 'new_bid_contract_years': 2})
    for user in users[2:]:
        drop_out_user({'admin_bid_override': False, 'team_name': user.team_name})
        
    # Match phase 1: Team 1 matches
    receive_auction_results_response({'results_response': 'rfa_owner_match_1_matched'})
    
    # Raise phase: Team 2 raises
    receive_auction_results_response({'results_response': 'rfa_bid_winner_raised', 'raise_bid': 7})
    
    # Match phase 2: Team 1 matches
    receive_auction_results_response({'results_response': 'rfa_owner_match_2_matched'})
    
    # Assert Team 1 wins at raised price
    drafted = drafted_player.objects.filter(full_name=dummy_player.full_name).first()
    assert drafted.team_drafted_by == team_1.team_name
    assert drafted.contract_price == 7
    assert drafted.years_drafted == 2

@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_end')
@patch('trist_draft.apps.auction_table.consumers.start_new_auction_at_bidder')
def test_rfa_uncontested_no_bids(mock_start, mock_send_end, mock_update, ten_team_league, dummy_player):
    """Scenario 5: Team 1 nominates -> Teams 2-10 drop out without bidding -> Team 1 automatically wins for $1."""
    manager, users, team_1 = _setup_rfa_auction(ten_team_league, dummy_player)
    
    submit_auction_player({'admin_bid_override': False, 'team_name': team_1.team_name, 'submitted_player_name': dummy_player.full_name, 'submitted_player_team': dummy_player.team, 'submitted_player_position': dummy_player.position})
    submit_new_bid({'admin_bid_override': False, 'team_name': team_1.team_name, 'new_bid': 1, 'new_bid_contract_years': 1})
    
    for user in users[1:]:
        drop_out_user({'admin_bid_override': False, 'team_name': user.team_name})
        
    # Assert Team 1 wins at initial price without needing match phases
    drafted = drafted_player.objects.filter(full_name=dummy_player.full_name).first()
    assert drafted.team_drafted_by == team_1.team_name
    assert drafted.contract_price == 1
    assert drafted.years_drafted == 1

@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_bidding_end')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_end')
@patch('trist_draft.apps.auction_table.consumers.start_new_auction_at_bidder')
def test_rfa_pass_then_bid_later(mock_start, mock_send_end, mock_send_bidding_end, mock_update, ten_team_league, dummy_player):
    """Scenario 6: Team 1 nominates -> Team 2 passes -> Team 3 bids -> Team 2 bids -> Everyone drops out -> Team 1 rejects -> Team 2 wins."""
    manager, users, team_1 = _setup_rfa_auction(ten_team_league, dummy_player)
    team_2 = users[1]
    team_3 = users[2]
    
    submit_auction_player({'admin_bid_override': False, 'team_name': team_1.team_name, 'submitted_player_name': dummy_player.full_name, 'submitted_player_team': dummy_player.team, 'submitted_player_position': dummy_player.position})
    submit_new_bid({'admin_bid_override': False, 'team_name': team_1.team_name, 'new_bid': 1, 'new_bid_contract_years': 1})
    
    pass_user({'admin_bid_override': False, 'team_name': team_2.team_name})
    submit_new_bid({'admin_bid_override': False, 'team_name': team_3.team_name, 'new_bid': 2, 'new_bid_contract_years': 1})
    
    # Teams 4-10 drop out
    for user in users[3:]:
        drop_out_user({'admin_bid_override': False, 'team_name': user.team_name})
        
    # Now it's Team 2's turn again (they passed earlier). Team 2 bids $5.
    submit_new_bid({'admin_bid_override': False, 'team_name': team_2.team_name, 'new_bid': 5, 'new_bid_contract_years': 1})
    
    # Team 3 drops out
    drop_out_user({'admin_bid_override': False, 'team_name': team_3.team_name})
    
    # Match phase 1: Team 1 rejects
    receive_auction_results_response({'results_response': 'rfa_owner_match_1_rejected'})
    
    drafted = drafted_player.objects.filter(full_name=dummy_player.full_name).first()
    assert drafted.team_drafted_by == team_2.team_name
    assert drafted.contract_price == 5
    assert drafted.years_drafted == 1

@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_bidding_end')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_end')
@patch('trist_draft.apps.auction_table.consumers.start_new_auction_at_bidder')
def test_rfa_pass_then_drop_out(mock_start, mock_send_end, mock_send_bidding_end, mock_update, ten_team_league, dummy_player):
    """Scenario 7: Team 2 passes -> Team 3 bids -> Turn back to Team 2 -> Team 2 drops out -> Team 3 wins."""
    manager, users, team_1 = _setup_rfa_auction(ten_team_league, dummy_player)
    team_2 = users[1]
    team_3 = users[2]
    
    submit_auction_player({'admin_bid_override': False, 'team_name': team_1.team_name, 'submitted_player_name': dummy_player.full_name, 'submitted_player_team': dummy_player.team, 'submitted_player_position': dummy_player.position})
    submit_new_bid({'admin_bid_override': False, 'team_name': team_1.team_name, 'new_bid': 1, 'new_bid_contract_years': 1})
    
    pass_user({'admin_bid_override': False, 'team_name': team_2.team_name})
    submit_new_bid({'admin_bid_override': False, 'team_name': team_3.team_name, 'new_bid': 5, 'new_bid_contract_years': 1})
    
    # Teams 4-10 drop out
    for user in users[3:]:
        drop_out_user({'admin_bid_override': False, 'team_name': user.team_name})
        
    # Team 2's turn again. Team 2 drops out.
    drop_out_user({'admin_bid_override': False, 'team_name': team_2.team_name})
    
    # Match phase 1: Team 1 rejects
    receive_auction_results_response({'results_response': 'rfa_owner_match_1_rejected'})
    
    drafted = drafted_player.objects.filter(full_name=dummy_player.full_name).first()
    assert drafted.team_drafted_by == team_3.team_name
    assert drafted.contract_price == 5
    assert drafted.years_drafted == 1

@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_bidding_end')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_end')
@patch('trist_draft.apps.auction_table.consumers.start_new_auction_at_bidder')
def test_rfa_pass_then_everyone_else_drops_out(mock_start, mock_send_end, mock_send_bidding_end, mock_update, ten_team_league, dummy_player):
    """Scenario 8: Team 2 passes -> everyone drops out. Current logic forces Owner to match and Player 2 gets chance to raise."""
    manager, users, team_1 = _setup_rfa_auction(ten_team_league, dummy_player)
    team_2 = users[1]
    
    submit_auction_player({'admin_bid_override': False, 'team_name': team_1.team_name, 'submitted_player_name': dummy_player.full_name, 'submitted_player_team': dummy_player.team, 'submitted_player_position': dummy_player.position})
    submit_new_bid({'admin_bid_override': False, 'team_name': team_1.team_name, 'new_bid': 1, 'new_bid_contract_years': 1})
    
    pass_user({'admin_bid_override': False, 'team_name': team_2.team_name})
    
    # Teams 3-10 drop out
    for user in users[2:]:
        drop_out_user({'admin_bid_override': False, 'team_name': user.team_name})
        
    # The current code in drop_out_user for this case simulates an automatic match by Team 1
    # Team 2 is then offered the chance to raise via rfa_no_bid_winner_raised.
    # If Team 2 decides NOT to raise (by dropping out), Team 1 keeps the player for the original $1.
    receive_auction_results_response({'results_response': 'rfa_bid_winner_dropped_out'})
    
    drafted = drafted_player.objects.filter(full_name=dummy_player.full_name).first()
    assert drafted.team_drafted_by == team_1.team_name
    assert drafted.contract_price == 1
    assert drafted.years_drafted == 1

@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_bidding_end')
@patch('trist_draft.apps.auction_table.consumers.send_rfa_auction_end')
@patch('trist_draft.apps.auction_table.consumers.start_new_auction_at_bidder')
def test_rfa_complex_bidding_sequence(mock_start_new, mock_send_end, mock_send_bidding_end, mock_update, ten_team_league, dummy_player):
    """
    Simulates a very chaotic bidding sequence with 20+ bids across multiple loops for RFA.
    Teams drop out slowly. Intermediate assertions check the exact state of active_bidder.
    Ends with the highest bidder winning after the owner rejects the match.
    """
    from trist_draft.apps.auction_table.consumers import submit_auction_player, submit_new_bid, drop_out_user, receive_auction_results_response
    
    manager, users, team_1 = _setup_rfa_auction(ten_team_league, dummy_player)
    
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
    assert manager.active_bidder == 2 # Skips t1 because t1 is the RFA owner
    
    # --- ROUND 2 ---
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
    assert manager.active_bidder == 3 # Skips t10 -> t1(owner) -> t2(dropped) -> t3
    
    # --- ROUND 3 (Only t3, t6, t8, t9 remain) ---
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
    
    # The moment t8 drops out, t3 is the highest bidder.
    # Check that bidding phase end was triggered
    mock_send_bidding_end.assert_called_once_with(t3, t1)
    
    # RFA Match phase: Team 1 (the owner) declines to match the $30 bid.
    receive_auction_results_response({'results_response': 'rfa_owner_match_1_rejected'})
    
    # Verify final drafted player
    drafted = drafted_player.objects.filter(full_name=dummy_player.full_name).first()
    assert drafted.team_drafted_by == t3
    assert drafted.contract_price == 30
    assert drafted.years_drafted == 1
