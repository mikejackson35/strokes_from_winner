import numpy as np
import pandas as pd
import datetime as dt
import plotly.express as px
import streamlit as st
import statsmodels.api as sm

config = {'displayModeBar': False}

dg_rankings = pd.read_csv("data/dg_rankings.csv")
stats = pd.read_csv("data/stats - Copy.csv")

dg_stats = stats.copy()
dg_rankings = dg_rankings.copy()

st.title('Strokes Behind Leader')

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
    
    fig = px.scatter(final_scores[final_scores.player_name==player].groupby(pd.Grouper(key='event_completed', freq='M'))['strokes_behind_winner'].mean().reset_index(),
                x='event_completed',
                y='strokes_behind_winner',
                # color='finish_pos',
                width=800,
                template='seaborn',
                trendline_color_override='black', trendline_options=dict(frac=0.4),
                trendline='lowess',
                labels={'event_completed':'Event Date','strokes_behind_winner':'Strokes Behind Winner','finish_pos':'Finish Position'},
                title=f'{player}').update_layout(title_x=0).add_hline(y=final_scores[final_scores.rank_bin=='1-100'].strokes_behind_winner.mean(), line_dash='dash', line_color='red', line_width=1)


    st.plotly_chart(fig, config=config)

    # ---- REMOVE UNWANTED STREAMLIT STYLING ----
# hide_st_style = """
#             <style>
#             Main Menu {visibility: hidden;}
#             footer {visibility: hidden;}
#             header {visibility: hidden;}
#             </style>
#             """
            
# st.markdown(hide_st_style, unsafe_allow_html=True)