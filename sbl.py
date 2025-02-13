import numpy as np
import pandas as pd
import datetime as dt
import plotly.express as px
import streamlit as st
import statsmodels.api as sm

config = {'displayModeBar': False}

dg_rankings = pd.read_csv("data/dg_rankings.csv")
stats = pd.read_csv("data/stats.csv")

dg_stats = stats.copy()
dg_rankings = dg_rankings.copy()

st.title('Strokes Behind Winner')
placeholder = st.empty()


###########################
#  SPLIT FROM DG_STATS TO MAKE LOSSES_DF ---> DATA

non_stat_cols = ['season','event_name','unique_event_id','event_completed','player_name','round_num','round_score','finish_pos']

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
player_rank_map = dict(zip(dg_rankings['player_name'],dg_rankings['datagolf_rank']))

final_scores['rank_bin'] = final_scores['player_name'].map(rank_map)
final_scores['player_rank'] = final_scores['player_name'].map(player_rank_map)

final_scores = final_scores[['season','event_name','event_completed','rank_bin','player_rank','player_name','finish_pos','r4_delta','rd_4_move','strokes_behind_winner']]

final_scores['event_completed'] = pd.to_datetime(final_scores['event_completed'])

# final_scores['year'] = final_scores['event_completed'].dt.year

top_100_players = final_scores[(final_scores.rank_bin=='1-100') | (final_scores.rank_bin=='101-200')].sort_values(by='player_rank').player_name.unique()

# header
avg = final_scores[(final_scores.rank_bin=='1-100') | (final_scores.rank_bin=='101-200')].strokes_behind_winner.mean().round(1)
with placeholder:
    st.caption(f'Top 200 Avg:  {avg}')


# Loop through each player in the top 100
for player in top_100_players: 

    final_scores['event_completed'] = pd.to_datetime(final_scores['event_completed'].dt.strftime('%Y-%m-%d'))

    recent_avg = round(final_scores[(final_scores.event_completed > '2023-09-01') & (final_scores.player_name==player)]
                       .strokes_behind_winner.mean(), 1)
    
    player_rank = int(final_scores[final_scores.player_name==player].player_rank.iloc[0])

    data = final_scores[
        (final_scores.player_name == player) & 
        (final_scores.event_completed > '2020-09-01')
    ].copy()

    # Create a continuous numerical year column
    data['year_continuous'] = data['event_completed'].dt.year  

    # Perform the grouping operation while preserving event dates
    grouped_data = data.groupby([pd.Grouper(key='event_completed', freq='W'), 'event_name','season'])[
        ['strokes_behind_winner', 'rd_4_move', 'year_continuous']
    ].mean().dropna().reset_index()

    # Convert 'year_continuous' to string for categorical coloring
    grouped_data['year_category'] = grouped_data['season'].astype(str)

    # ✅ Compute the rolling trendline manually (ensures continuity across years)
    grouped_data['rolling_avg'] = grouped_data['strokes_behind_winner'].rolling(window=16, min_periods=16).mean()


    grouped_data['event_month_year'] = grouped_data['event_completed'].dt.strftime('%b %Y')  # 'Aug 2023' format



    # Scatter plot with year as a color category
    fig = px.scatter(

        grouped_data,
        x='event_completed',
        y='strokes_behind_winner',
        width=800,
        height=400,
        template='plotly_dark',
        color='year_category',  # Categorical coloring
        hover_name='event_name',
        hover_data={'year_category': False},  
        labels={'event_month_year': '', 'strokes_behind_winner': 'Strokes Back', 'event_completed':''},  # Remove the column label
        title=f'#{player_rank} {player}<br>Avg - {recent_avg}'

    ).update_layout(

        title_x=0, 
        yaxis=dict(range=[-1, 30]),
        title={'font': {'size': 20}},
        # xaxis_title='Event Date',
        yaxis_title='Strokes Behind Winner',
        hoverlabel=dict(font_size=12),
        font=dict(size=12),
        # legend=dict(title=' ', orientation='h', y=1.1, x=0.2),

    ).add_hline(

        y=final_scores[(final_scores.rank_bin=='1-100') | (final_scores.rank_bin=='101-200')]
        .strokes_behind_winner.mean(), 
        line_dash='dash', line_color='red', line_width=1, 
        annotation_text='Top 200 Avg', annotation_position='top left', 
        annotation_font_size=12, annotation_font_color='IndianRed'

    ).update_yaxes(

        showgrid=True, gridwidth=1, gridcolor='LightGray'

    ).update_traces(marker=dict(size=8)) 

    # Add a trendline to the scatter plot
    fig.add_trace(
        px.line(
            grouped_data,
            x='event_completed',
            y='rolling_avg'
        ).data[0]
    )
    fig.data[-1].line.color = 'black'  # Ensure trendline is black
    fig.data[-1].line.width = 2  # Adjust thickness of the line



    # Wrap each chart in a bordered container
    with st.container(border=True):
        st.plotly_chart(fig, config=config, use_container_width=True)


    # ---- REMOVE UNWANTED STREAMLIT STYLING ----
hide_st_style = """
            <style>
            Main Menu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
            
st.markdown(hide_st_style, unsafe_allow_html=True)