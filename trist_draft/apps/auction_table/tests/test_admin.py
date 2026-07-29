import pytest
from unittest.mock import patch
from trist_draft.apps.auction_table.models import auction_user, auction_manager, drafted_player, nfl_player
from trist_draft.apps.auction_table.consumers import (
    admin_force_pass,
    admin_force_dropout,
    admin_toggle_bathroom_mode,
    admin_undo_draft,
    admin_update_budget,
    admin_resync_roster,
    admin_start_phase,
    admin_pass_player_selection,
    admin_dropout_player_selection,
    admin_toggle_pass_available,
    admin_undropout_bidding,
    admin_undropout_selection,
)

pytestmark = pytest.mark.django_db


@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
def test_admin_force_pass(mock_update, ten_team_league):
    """Test admin can force pass on behalf of a team."""
    team_1 = ten_team_league['users'][0]
    manager = ten_team_league['manager']
    manager.active_bidder = 1
    manager.save()

    # Force pass for target team
    admin_force_pass({'target_team': team_1.team_name})
    team_1.refresh_from_db()
    assert team_1.pass_available is False


@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
def test_admin_force_dropout(mock_update, ten_team_league):
    """Test admin can force a team to drop out."""
    team_1 = ten_team_league['users'][0]

    admin_force_dropout({'target_team': team_1.team_name})
    team_1.refresh_from_db()
    assert team_1.still_in_auction is False


@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
def test_admin_pass_player_selection(mock_update, ten_team_league):
    """Test admin can force pass player selection for active bidder."""
    manager = ten_team_league['manager']
    manager.active_bidder = 1
    manager.initiated_auction = 1
    manager.save()

    admin_pass_player_selection({})
    manager.refresh_from_db()
    assert manager.active_bidder == 2


@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
def test_admin_dropout_player_selection(mock_update, ten_team_league):
    """Test admin can force dropout of player selection for active bidder."""
    team_1 = ten_team_league['users'][0]
    manager = ten_team_league['manager']
    manager.active_bidder = 1
    manager.initiated_auction = 1
    manager.save()

    admin_dropout_player_selection({})
    team_1.refresh_from_db()
    manager.refresh_from_db()
    assert team_1.dropped_out_of_selection is True
    assert manager.active_bidder == 2


@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
def test_admin_toggle_pass_available(mock_update, ten_team_league):
    """Test admin can toggle pass available state for a team."""
    team_1 = ten_team_league['users'][0]
    assert team_1.pass_available is True

    admin_toggle_pass_available({'target_team': team_1.team_name, 'state': False})
    team_1.refresh_from_db()
    assert team_1.pass_available is False

    admin_toggle_pass_available({'target_team': team_1.team_name, 'state': True})
    team_1.refresh_from_db()
    assert team_1.pass_available is True


@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
def test_admin_undropout_bidding(mock_update, ten_team_league):
    """Test admin can restore a dropped out team back to active bidding."""
    team_1 = ten_team_league['users'][0]
    team_1.still_in_auction = False
    team_1.dropped_out_of_bid_early = True
    team_1.save()

    admin_undropout_bidding({'target_team': team_1.team_name})
    team_1.refresh_from_db()
    assert team_1.still_in_auction is True
    assert team_1.dropped_out_of_bid_early is False


@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
def test_admin_undropout_selection(mock_update, ten_team_league):
    """Test admin can restore a team dropped out of selection back to active selection."""
    team_1 = ten_team_league['users'][0]
    team_1.dropped_out_of_selection = True
    team_1.save()

    admin_undropout_selection({'target_team': team_1.team_name})
    team_1.refresh_from_db()
    assert team_1.dropped_out_of_selection is False


@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
def test_admin_toggle_bathroom_mode(mock_update, ten_team_league):
    """Test admin can toggle bathroom mode for a team."""
    team_1 = ten_team_league['users'][0]
    assert team_1.bathroom_mode_enabled is False

    admin_toggle_bathroom_mode({'target_team': team_1.team_name, 'state': True})
    team_1.refresh_from_db()
    assert team_1.bathroom_mode_enabled is True

    admin_toggle_bathroom_mode({'target_team': team_1.team_name, 'state': False})
    team_1.refresh_from_db()
    assert team_1.bathroom_mode_enabled is False


@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
def test_admin_update_budget(mock_update, ten_team_league):
    """Test admin can update a user's budget."""
    team_1 = ten_team_league['users'][0]
    team_1.budget_remaining = 100
    team_1.save()

    admin_update_budget({'target_team': team_1.team_name, 'new_budget': 150})
    team_1.refresh_from_db()
    assert team_1.budget_remaining == 150


@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
def test_admin_start_phase(mock_update, ten_team_league):
    """Test admin can initiate a new draft phase."""
    manager = ten_team_league['manager']

    admin_start_phase({'phase': 'ufa', 'start_bidder': 3})
    manager.refresh_from_db()
    assert manager.auction_type == 'ufa'
    assert manager.active_bidder == 3


@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
def test_admin_undo_draft_ufa(mock_update, ten_team_league, dummy_player):
    """Test undoing a drafted UFA player refunds budget and resets nfl_player status."""
    team_1 = ten_team_league['users'][0]
    team_1.budget_remaining = 80
    team_1.save()

    dummy_player.drafted_by = team_1.team_name
    dummy_player.save()

    dp = drafted_player.objects.create(
        team=dummy_player.team,
        position=dummy_player.position,
        full_name=dummy_player.full_name,
        team_drafted_by=team_1.team_name,
        years_drafted=2,
        contract_price=20,
        is_rookie=False,
        draft_type='ufa'
    )

    admin_undo_draft()

    team_1.refresh_from_db()
    dummy_player.refresh_from_db()

    assert team_1.budget_remaining == 100  # 80 + 20 refund
    assert dummy_player.drafted_by == 'Undrafted'
    assert drafted_player.objects.filter(pk=dp.pk).exists() is False


@patch('trist_draft.apps.auction_table.consumers.update_auction_table')
def test_admin_undo_draft_rfa(mock_update, ten_team_league, dummy_player):
    """Test undoing a drafted RFA player restores the player to the owner's RFA list."""
    team_1 = ten_team_league['users'][0]
    team_2 = ten_team_league['users'][1]

    # Team 1 originally owned dummy_player as RFA
    team_1.initial_rfa_list = [dummy_player.player_id]
    team_1.current_rfa_list = []  # player was drafted so removed from current list
    team_1.rfas_remaining = 0
    team_1.save()

    team_2.budget_remaining = 50
    team_2.save()

    dummy_player.drafted_by = team_2.team_name
    dummy_player.save()

    dp = drafted_player.objects.create(
        team=dummy_player.team,
        position=dummy_player.position,
        full_name=dummy_player.full_name,
        team_drafted_by=team_2.team_name,
        years_drafted=1,
        contract_price=15,
        is_rookie=False,
        draft_type='rfa'
    )

    admin_undo_draft()

    team_1.refresh_from_db()
    team_2.refresh_from_db()
    dummy_player.refresh_from_db()

    assert team_2.budget_remaining == 65  # 50 + 15
    assert dummy_player.drafted_by == 'Undrafted'
    assert dummy_player.player_id in team_1.current_rfa_list
    assert team_1.rfas_remaining == 1
    assert drafted_player.objects.filter(pk=dp.pk).exists() is False
