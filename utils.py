import pandas as pd


def process_raw_stats(raw_stats):
    # Create unique_event_id
    raw_stats['unique_event_id'] = raw_stats['season'].astype(str) + raw_stats['event_id'].astype(str)

    # Add score to par column and remove rounds with scores less than 40
    raw_stats['score_to_par'] = raw_stats['round_score'] - raw_stats['course_par']
    raw_stats.drop(raw_stats[raw_stats['round_score'] < 40].index, inplace=True)

    # Remove text from 'finish_pos' column
    raw_stats['finish_pos'] = pd.to_numeric(raw_stats['fin_text'].str.replace("T",""), errors='coerce')
    raw_stats.drop(columns=['fin_text'], inplace=True)
    
    # fix dtype
    raw_stats['event_completed'] = pd.to_datetime(raw_stats['event_completed'])

    # Create 'loser_key' column
    raw_stats['loser_key'] = list(zip(raw_stats['player_name'].astype(str), raw_stats['unique_event_id'].astype(str)))

    return raw_stats