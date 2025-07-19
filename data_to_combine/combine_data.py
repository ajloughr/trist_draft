import pandas as pd
import os
import re

# Team abbreviation to long name mapping
team_mapping = {
    'ARI': 'Cardinals', 'ATL': 'Falcons', 'BAL': 'Ravens', 'BUF': 'Bills', 'CAR': 'Panthers',
    'CHI': 'Bears', 'CIN': 'Bengals', 'CLE': 'Browns', 'DAL': 'Cowboys', 'DEN': 'Broncos',
    'DET': 'Lions', 'GB': 'Packers', 'HOU': 'Texans', 'IND': 'Colts', 'JAX': 'Jaguars',
    'KC': 'Chiefs', 'LV': 'Raiders', 'LAC': 'Chargers', 'LAR': 'Rams', 'MIA': 'Dolphins',
    'MIN': 'Vikings', 'NE': 'Patriots', 'NO': 'Saints', 'NYG': 'Giants', 'NYJ': 'Jets',
    'PHI': 'Eagles', 'PIT': 'Steelers', 'SEA': 'Seahawks', 'SF': '49ers', 'TB': 'Buccaneers',
    'TEN': 'Titans', 'WAS': 'Commanders', 'FA': 'Free Agent', 'RE': 'Retired', 'CA': 'Canada'
}

# Manual mapping for players without teams
player_team_mapping = {
    'Kareem Hunt': 'FA',
    'Dalvin Cook': 'FA',
    'Michael Thomas': 'FA',
    'Kenyan Drake': 'RE',
    'Makai Polk': 'CA',
    'Darren Waller': 'RE',
    'Hunter Renfrow': 'FA',
    'Jerick McKinnon': 'FA'
}

def load_csv(filename):
    try:
        df = pd.read_csv(filename)
        print(f"Loaded {filename} successfully.")
        return df
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return None

def clean_numeric_columns(df):
    for col in df.columns:
        if col not in ['Player', 'Team', 'POS', 'drafted_by']:
            df[col] = df[col].replace({',': ''}, regex=True)  # Remove commas
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(float)
    return df

def clean_pos_column(df):
    df['POS'] = df['POS'].str.replace('\d+', '', regex=True)
    return df

def update_defense_teams(df):
    for index, row in df.iterrows():
        if row['Team'] == 'DST':
            team_name = row['Player'].split()[-1]
            team_abbr = [abbr for abbr, name in team_mapping.items() if name == team_name]
            if team_abbr:
                df.at[index, 'Team'] = team_abbr[0]
    return df

def get_next_version_filename(base_filename):
    # Get the current working directory
    cwd = os.getcwd()

    # Get the base name and current version
    base_name, current_version = re.match(r"(.*)_v(\d+)", base_filename).groups()
    current_version = int(current_version)

    # Get all files in the current directory
    files = os.listdir(cwd)

    # Find the highest version number for files with the same base name
    highest_version = current_version
    for file in files:
        match = re.match(rf"{re.escape(base_name)}_v(\d+)", file)
        if match:
            version = int(match.group(1))
            if version > highest_version:
                highest_version = version

    # Increment the highest version number by 1 for the new version
    next_version = highest_version + 1
    next_version_filename = f"{base_name}_v{next_version}.csv"
    return next_version_filename

# Get the current working directory
cwd = os.getcwd()

# Load the overall ADP rankings
adp_file = os.path.join(cwd, 'FantasyPros_2024_Overall_ADP_Rankings.csv')
adp_df = load_csv(adp_file)

# Load all other datasets
datasets = {
    'K': load_csv(os.path.join(cwd, 'FantasyPros_Fantasy_Football_Projections_K.csv')),
    'QB': load_csv(os.path.join(cwd, 'FantasyPros_Fantasy_Football_Projections_QB.csv')),
    'RB': load_csv(os.path.join(cwd, 'FantasyPros_Fantasy_Football_Projections_RB.csv')),
    'TE': load_csv(os.path.join(cwd, 'FantasyPros_Fantasy_Football_Projections_TE.csv')),
    'WR': load_csv(os.path.join(cwd, 'FantasyPros_Fantasy_Football_Projections_WR.csv')),
    'DST': load_csv(os.path.join(cwd, 'FantasyPros_Fantasy_Football_Projections_DST.csv')),
    'FLX': load_csv(os.path.join(cwd, 'FantasyPros_Fantasy_Football_Projections_FLX.csv'))
}

# Add a 'POS' column to each dataset based on the filename
for position, df in datasets.items():
    if df is not None:
        if 'POS' not in df.columns:
            df['POS'] = position
        df = clean_numeric_columns(df)
        df = clean_pos_column(df)

# Function to merge datasets and add missing players from specific projections
def merge_datasets(adp_df, datasets):
    merged_df = adp_df.copy()
    
    for position, df in datasets.items():
        if df is None:
            continue
        
        df['POS'] = position
        for col in df.columns:
            if col not in ['Player', 'Team', 'POS']:
                new_col = f"{col}_{position.lower()}" if col in merged_df.columns else col
                merged_df[new_col] = merged_df.apply(
                    lambda row: df.loc[(df['Player'] == row['Player']) & (df['Team'] == row['Team']), col].values[0]
                    if ((df['Player'] == row['Player']) & (df['Team'] == row['Team'])).any() else row.get(new_col, ''),
                    axis=1
                )
        # Add missing players from the specific dataset
        missing_players = df[~df['Player'].isin(merged_df['Player'])]
        merged_df = pd.concat([merged_df, missing_players], ignore_index=True, sort=False)
    
    return merged_df

# Merge datasets and add missing players
if adp_df is not None:
    final_df = merge_datasets(adp_df, datasets)
    
    # Ensure all numeric columns are floats
    final_df = clean_numeric_columns(final_df)
    
    # Add a 'drafted_by' column with a default value of 'Undrafted'
    final_df['drafted_by'] = 'Undrafted'
    
    # Update team information for players without teams
    for player, team in player_team_mapping.items():
        final_df.loc[final_df['Player'] == player, 'Team'] = team
    
    # Update team names for defenses
    final_df = update_defense_teams(final_df)
    
    # Correct JAC to JAX
    final_df['Team'] = final_df['Team'].replace('JAC', 'JAX')
    
    # Add the long team names
    final_df['team_long_name'] = final_df['Team'].map(team_mapping)
    
    # Remove rows where 'Player' field has less than 3 characters
    final_df = final_df[final_df['Player'].str.len() >= 3]
    
    # Reorder columns
    final_df = final_df[['Rank', 'Player', 'Team', 'team_long_name'] + [col for col in final_df.columns if col not in ['Rank', 'Player', 'Team', 'team_long_name', 'drafted_by']] + ['drafted_by']]
    
    # Determine the next version filename
    base_filename = 'Final_Updated_Fantasy_Football_Projections_v1.csv'
    final_output_file = os.path.join(cwd, get_next_version_filename(base_filename))
    
    # Save the final merged dataframe to CSV
    final_df.to_csv(final_output_file, index=False)
    print(f"Saved final dataframe to {final_output_file}")
    
    # Generate the correct COPY command
    final_columns = final_df.columns.str.lower().tolist()
    
    copy_command = f"""
    COPY auction_table_nfl_player({', '.join(final_columns)})
    FROM '{final_output_file}' 
    DELIMITER ',' 
    CSV HEADER;
    """
    
    # Print the COPY command in one line
    copy_command = ' '.join(copy_command.split())
    print(copy_command)
else:
    print("Failed to load the overall ADP rankings.")
