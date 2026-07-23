from django.test import TestCase
from django.contrib.auth.models import User
from trist_draft.apps.auction_table.models import auction_user, auction_manager, nfl_player, drafted_player
from trist_draft.apps.auction_table.consumers import submit_auction_player
from django.core.management import call_command

class RookieDraftTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up shared data for all test methods (faster than setUp)
        cls.teams = []
        for i in range(1, 9):
            user = User.objects.create_user(username=f'user{i}', password='pass')
            team = auction_user.objects.create(
                team_name=f"Team {i}",
                draft_order=i,
                budget_remaining=100,
                starting_budget=100,
                user=user
            )
            cls.teams.append(team)

        cls.manager = auction_manager.objects.create(
            pk=1,
            auction_type='rookie',
            rookie_draft_order=[1, 2, 3, 4, 5, 6, 7, 8, 8, 7, 6, 5, 4, 3, 2, 1],
            rookie_draft_current_position=0,
            active_bidder=1
        )

        # Get 10 real, undrafted players from the DB
        cls.available_players = list(
            nfl_player.objects.filter(drafted_by="Undrafted")[:10]
        )
        assert len(cls.available_players) >= 10, "Not enough undrafted players in DB"

    def test_rookie_draft_player_submission(self):
        team = self.teams[0]
        player = self.available_players[0]

        player_data = {
            'team_name': team.team_name,
            'submitted_player_name': player.full_name,
            'submitted_player_team': player.team,
            'submitted_player_position': player.position,
            'admin_bid_override': False
        }

        submit_auction_player(player_data)

        # Confirm drafted_player entry
        drafted = drafted_player.objects.get(full_name=player.full_name)
        self.assertEqual(drafted.team_drafted_by, team.team_name)
        self.assertEqual(drafted.contract_price, 1)
        self.assertTrue(drafted.is_rookie)

        # Confirm nfl_player updated
        updated_player = nfl_player.objects.get(full_name=player.full_name)
        self.assertEqual(updated_player.drafted_by, team.team_name)

        # Confirm budget deducted
        updated_team = auction_user.objects.get(team_name=team.team_name)
        self.assertEqual(updated_team.budget_remaining, 99)

    def test_full_rookie_draft_sequence(self):
        draft_order = self.manager.rookie_draft_order

        for pick_num in range(len(draft_order)):
            self.manager.refresh_from_db()
            current_draft_order = draft_order[self.manager.rookie_draft_current_position]
            current_team = next(t for t in self.teams if t.draft_order == current_draft_order)
            player = self.available_players[pick_num % len(self.available_players)]  # Reuse if fewer than 16

            player_data = {
                'team_name': current_team.team_name,
                'submitted_player_name': player.full_name,
                'submitted_player_team': player.team,
                'submitted_player_position': player.position,
                'admin_bid_override': False
            }

            submit_auction_player(player_data)

            drafted = drafted_player.objects.get(full_name=player.full_name)
            self.assertEqual(drafted.team_drafted_by, current_team.team_name)

            updated_player = nfl_player.objects.get(full_name=player.full_name)
            self.assertEqual(updated_player.drafted_by, current_team.team_name)

        self.manager.refresh_from_db()
        self.assertEqual(self.manager.active_bidder, 0)
