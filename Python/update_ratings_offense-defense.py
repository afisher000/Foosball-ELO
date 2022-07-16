# -*- coding: utf-8 -*-
"""
Created on Sat May 14 12:26:06 2022

@author: afish
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

today = datetime.strptime('07/05/2022', '%m/%d/%Y')
players = np.array([
    'atharva',  'andy',     'alex',     'sophie',   'pietro',
    'lucy',     'paul',     'lawler',   'max',      'andonian',
    'eric',     'jake',     'obed',     'pratik',   'fabio',
    'VOID'])

# 1000 Initial Rating for offense and defense
rating_hist = pd.DataFrame(np.zeros((1,len(players))), columns=players)
rating_hist = rating_hist.join(rating_hist, lsuffix='_off', rsuffix='_def')

# Read gamelog
gamelog = pd.read_csv('Game Log.csv')
gamelog.Date = gamelog.Date.map(lambda x: datetime.strptime(x, '%m/%d/%Y'))

# Drop singles games
singles = (gamelog.WO==gamelog.WD) | (gamelog.LO==gamelog.LD)
gamelog = gamelog[~singles] 

# Check gamelog names are correct
name_errors = (~gamelog[['WO','WD','LO','LD']].isin(players)).any(axis=1)
if name_errors.sum()>0:
    print(gamelog.loc[name_errors])
    raise Exception('These rows have unidentified players.\n')
    
# Check gamelog scores are correct
score_errors = ~gamelog.Score.isin(range(10))
if score_errors.sum()>0:
    print(gamelog.loc[score_errors])
    raise Exception('These rows have an incorrect score...\n')
    
# Update Ratings
spread = 200
k = 64
for idx, game in gamelog.iterrows():
    if idx==0:
        game_ratings = pd.Series(1000*np.ones(len(rating_hist.columns)), index=rating_hist.columns)
    else:
        game_ratings = rating_hist.loc[idx-1]
    print(idx)
    
    # Compute actual and expected point-win ratios
    W_rating = game_ratings[game.WO+'_off']/2 + game_ratings[game.WD+'_def']/2
    L_rating = game_ratings[game.LO+'_off']/2 + game_ratings[game.LD+'_def']/2
    actual_win_ratio = 10/(game.Score+10)
    expected_win_ratio = (1+10**((L_rating-W_rating)/spread))**(-1)
    rating_change = round(k*(actual_win_ratio-expected_win_ratio))
    
    # Update ratings (check for singles)
    game_ratings[game.WO+'_off']+= rating_change
    game_ratings[game.LO+'_off']-= rating_change
    game_ratings[game.WD+'_def']+= rating_change 
    game_ratings[game.LD+'_def']-= rating_change
    game_ratings['VOID'] = 1000 #VOID rating never changes
    rating_hist.loc[idx] = game_ratings
    


# Find active players in last month
last_month_games = gamelog[gamelog.Date>(today-timedelta(30))]
active_players = np.unique(last_month_games[['WO','WD','LO','LD']])

# Find change in rating and ranking for active players
prev_rating_hist = rating_hist[gamelog.Date<(today-timedelta(7))]
cur_rating_hist = rating_hist[gamelog.Date<=today]

# CHECK IF THIS IS CORRECTLY MAKING A DATAFRAME
ratings = pd.DataFrame()
ratings['offense'] = [cur_rating_hist[name+'_off'].iloc[-1] for name in active_players]
ratings['defense'] = [cur_rating_hist[name+'_def'].iloc[-1] for name in active_players]
ratings['total'] = ratings.offense/2 + ratings.defense/2
ratings['prev_offense'] = [prev_rating_hist[name+'_off'].iloc[-1] for name in active_players]
ratings['prev_defense'] = [prev_rating_hist[name+'_def'].iloc[-1] for name in active_players]
ratings['prev_total'] = ratings.prev_offense/2 + ratings.prev_defense/2
ratings['rating_change'] = ratings.total - ratings.prev_total
ratings['name'] = active_players
ratings['rank'] = ratings.total.rank(ascending=False, method='min')
ratings['prev_rank'] = ratings.prev_total.rank(ascending=False, method='min')
ratings['rank_change'] = ratings['rank'] - ratings['prev_rank']


# Write weekly results to csv
# =============================================================================
# week_results_dict = {'Name':cur_ratings.index,
#                      'Rank':cur_ratings.rank(ascending=False, method='min'),
#                      'Rank Change':diff_rankings,
#                      'Rating':cur_ratings.values,
#                      'Rating Change':diff_ratings}
# week_results_df = pd.DataFrame(week_results_dict)
# week_results_df.sort_values('Rank', inplace=True)
# week_results_df.to_csv('week_results.csv', index=False)
# =============================================================================


## Further analysis
def compute_stats(gamelog, players, game_limit=20):
    entries = ['Games','Wins','Losses','OffWins','OffLosses','DefWins','DefLosses',
             'WinPct','LossPct','OffWinPct','DefWinPct','PointsFor','PointsAgainst',
             'PointsDiff','PointMargin']
    
    stats = pd.DataFrame(index = entries)
    
    # If no players specified, return empty df
    if len(players)==0:
        return stats
    
    for player in players:
        offwins, defwins, offlosses, deflosses, _ = (gamelog==player).sum()
        wins = offwins + defwins
        losses = offlosses + deflosses
        offwinpct = np.nan if (offwins+offlosses==0) else offwins/(offwins+offlosses)
        defwinpct = np.nan if (defwins+deflosses==0) else defwins/(defwins+deflosses)
            
        games = wins + losses
        Pfor = wins*10 + gamelog.Score[(gamelog.LO==player)|(gamelog.LD==player)].sum()
        Pagainst = losses*10 + gamelog.Score[(gamelog.WO==player)|(gamelog.WD==player)].sum()
        Pdiff = Pfor-Pagainst
        Pmargin = Pdiff/games
        player_entries = np.array([games, wins, losses, offwins, offlosses,
                                   defwins, deflosses, wins/games, losses/games,
                                   offwinpct, defwinpct,
                                   Pfor, Pagainst, Pdiff, Pmargin])
        stats[player] = player_entries
    stats = stats.T
    stats.drop( stats.index[stats.Games<game_limit], inplace=True ) #Remove rare players
    return stats

def get_matchup(gamelog, players):
    player1, player2, *_ = players
    possible_matchups = (gamelog==player1).any(axis=1)&(gamelog==player2).any(axis=1)
    player1_wins = (gamelog.WO==player1)|(gamelog.WD==player1)
    player2_wins = (gamelog.WO==player2)|(gamelog.WD==player2)
    matchups = (player1_wins^player2_wins)&possible_matchups
    
    if not matchups.any():
        return None
    stats = compute_stats(gamelog[matchups], players, 0)
    return stats

def get_all_matchups(gamelog, player1, players):
    
    stats = compute_stats(gamelog, [])
    for player in players:
        matchup_stats = get_matchup(gamelog, [player1, player])
        if matchup_stats is not None:
            stats[f'vs. {player}'] = matchup_stats.T[player1]
    
    return stats.T
    
#stats = compute_stats(gamelog, players)
#stats = get_all_matchups(gamelog, 'andy', players)










