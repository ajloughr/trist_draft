import csv
import sys
import os
import django

# Setup Django environment
sys.path.append('/code')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trist_draft.settings')
django.setup()

from django.contrib.auth.models import User
from trist_draft.apps.auction_table.models import auction_user, auction_manager

csv_file = '/code/draft_data/users.csv'

with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        username = row['username'].strip()
        password = row['password'].strip()
        is_admin = row['is_admin'].strip().lower() in ('true', '1', 't', 'y', 'yes')
        team_name = row['team_name'].strip()
        draft_order = int(row['draft_order'].strip())
        
        # Parse starting budget safely to handle strings like "$89.00"
        raw_budget = row['starting_budget'].strip().replace('$', '').replace(',', '')
        starting_budget = int(float(raw_budget))
        
        # Parse initial_rfa_list
        rfa_str = row.get('initial_rfa_list', '').strip()
        rfa_list = []
        if rfa_str:
            rfa_list = [int(x.strip()) for x in rfa_str.split(';') if x.strip().isdigit()]

        # Create or get user
        user, created = User.objects.get_or_create(username=username)
        user.set_password(password)
        if is_admin:
            user.is_staff = True
            user.is_superuser = True
        user.save()

        # Create or update auction_user
        au, au_created = auction_user.objects.get_or_create(user=user)
        au.team_name = team_name
        au.draft_order = draft_order
        au.starting_budget = starting_budget
        au.budget_remaining = starting_budget
        au.initial_rfa_list = rfa_list
        au.current_rfa_list = rfa_list
        au.rfas_remaining = len(rfa_list)
        au.save()
        
        print(f"Set up user '{username}' for team '{team_name}' with budget {starting_budget} and {len(rfa_list)} RFAs.")

# Also ensure auction_manager exists
manager, m_created = auction_manager.objects.get_or_create(pk=1)
# Generate a standard 1-10 snake draft order (3 rounds)
draft_order = [1,2,3,4,5,6,7,8,9,10, 10,9,8,7,6,5,4,3,2,1, 1,2,3,4,5,6,7,8,9,10]
manager.rookie_draft_order = draft_order
manager.save()

if m_created:
    print("Created initial auction_manager row.")
else:
    print("auction_manager row already exists and updated rookie order.")

print("User import complete!")
