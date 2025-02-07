import numpy as np
import pandas as pd
import datetime as dt
import plotly.express as px
import streamlit as st

dg_rankings = pd.read_csv("data/dg_rankings.csv")
stats = pd.read_csv("data/stats - Copy.csv")

dg_stats = stats.copy()
dg_rankings = dg_rankings.copy()

# remove text from 'finish_pos'
dg_stats['fin_text'] = pd.to_numeric(dg_stats['fin_text'].str.replace("T",""), errors='coerce')
dg_stats.rename(columns={'fin_text':"finish_pos"}, inplace=True) 

# make unique event identifier
dg_stats['unique_event_id'] = dg_stats['season'].astype(str) + dg_stats['event_id'].astype(str)

# add score to par column
dg_stats['score_to_par'] = dg_stats['round_score'] - dg_stats['course_par']
dg_stats.drop(dg_stats[dg_stats.round_score < 40].index, inplace=True)

###########################
#  SPLIT FROM DG_STATS TO MAKE LOSSES_DF ---> DATA

non_stat_cols = ['event_name','unique_event_id','event_completed','player_name','round_num','round_score','finish_pos']

# leaderboard thru 3 rounds of all tournaments
temp = dg_stats[dg_stats.round_num < 4][non_stat_cols].sort_values(['event_completed','player_name','round_num','round_score'])
temp['3_rd_score'] = temp.groupby(['player_name','unique_event_id'])['round_score'].cumsum(axis=0)
leaderboard_after_3 = temp[temp.round_num==3].sort_values(['unique_event_id', '3_rd_score']) # keeping for leaderboard thru 3 rounds

# # r4_delta column 
leader_score = leaderboard_after_3.groupby('unique_event_id')[['unique_event_id','3_rd_score']].min().reset_index(drop=True)
leaderboard_after_3 = pd.merge(leaderboard_after_3,leader_score,on='unique_event_id').rename(columns={'3_rd_score_x':'score_thru_3','3_rd_score_y':'leader_score'})
leaderboard_after_3['r4_delta'] = leaderboard_after_3.score_thru_3 - leaderboard_after_3.leader_score
leaderboard_after_3 = leaderboard_after_3.drop(columns='leader_score')

# leaderboard thru 3 rounds of all tournaments
temp = dg_stats[dg_stats.round_num < 5][non_stat_cols].sort_values(['event_completed','player_name','round_num','round_score'])
temp['4_rd_score'] = temp.groupby(['player_name','unique_event_id'])['round_score'].cumsum(axis=0)
leaderboard_after_4 = temp[temp.round_num==4][['unique_event_id','player_name','4_rd_score']] # keeping for leaderboard thru 3 rounds

# r4_delta column 
leader_score = leaderboard_after_4.groupby('unique_event_id')[['unique_event_id','4_rd_score']].min().reset_index(drop=True)
leaderboard_after_4 = pd.merge(leaderboard_after_4,leader_score,on='unique_event_id').rename(columns={'4_rd_score_x':'score_thru_4','4_rd_score_y':'winning_score'})#.drop(columns='4_rd_score_y')

final_scores = pd.merge(leaderboard_after_3,leaderboard_after_4, how='left', on=['unique_event_id','player_name'])

final_scores['strokes_behind_winner'] = final_scores.score_thru_4 - final_scores.winning_score

final_scores['rd_4_move'] = final_scores['r4_delta'] - final_scores['strokes_behind_winner']

# # data golf rankings bins by 100
bins100 = [0, 100, 200, 300, 400, 500]
labels100 = ['1-100', '101-200', '201-300', '301-400', '401-500']
dg_rankings['bin_100'] = pd.cut(dg_rankings['datagolf_rank'], bins=bins100, labels=labels100)

rank_map = dict(zip(dg_rankings['player_name'],dg_rankings['bin_100']))

final_scores['rank_bin'] = final_scores['player_name'].map(rank_map)

final_scores = final_scores[['event_name','event_completed','rank_bin','player_name','finish_pos','r4_delta','rd_4_move','strokes_behind_winner']]

final_scores['event_completed'] = pd.to_datetime(final_scores['event_completed'])

top_100_players = final_scores[final_scores.rank_bin=='1-100'].groupby('player_name',as_index=False)['finish_pos'].mean().sort_values(by='finish_pos').player_name.unique()

for player in top_100_players: 

    final_scores['event_completed'] = pd.to_datetime(final_scores['event_completed'])
    
    fig = px.scatter(final_scores[final_scores.player_name==player].groupby([pd.Grouper(key='event_completed', freq='M'), 'finish_pos']).mean().reset_index(),
                x='event_completed',
                y='strokes_behind_winner',
                # color='finish_pos',
                width=900,
                template='plotly_white',
                trendline_color_override='black',
                trendline='lowess',
                # color_continuous_scale='viridis',
                title=f'Strokes Behind Winner<br>{player}').add_hline(y=final_scores[final_scores.rank_bin=='1-100'].strokes_behind_winner.median(), line_dash='dash', line_color='pink')


    st.plotly_chart(fig)