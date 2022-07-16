# -*- coding: utf-8 -*-
"""
Created on Sat May 14 12:26:06 2022

@author: afish
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def simulate_games(today):
    stop_date = datetime.strptime(today, '%m/%d/%Y')
    players = np.array([
        'atharva',  'andy',     'alex',     'sophie',   'pietro',
        'lucy',     'paul',     'lawler',   'max',      'andonian',
        'eric',     'jake',     'obed',     'pratik',   'stefano',
        'fabio',    'VOID'])
    
    # 1000 Initial Rating
    ratings = pd.DataFrame(np.zeros((1,len(players))), columns=players)
    
    # Read gamelog
    gamelog = pd.read_csv('Game Log.csv')
    gamelog.Date = gamelog.Date.map(lambda x: datetime.strptime(x, '%m/%d/%Y'))
    
    # Drop singles games
    singles = (gamelog.WO==gamelog.WD) & (gamelog.LO==gamelog.LD)
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
            game_ratings = pd.Series(1000*np.ones(len(players)), index=players)
        else:
            game_ratings = ratings.loc[idx-1]
        
        # Compute actual and expected point-win ratios
        W_rating = game_ratings[game.WO]/2 + game_ratings[game.WD]/2
        L_rating = game_ratings[game.LO]/2 + game_ratings[game.LD]/2
        actual_win_ratio = 10/(game.Score+10)
        expected_win_ratio = (1+10**((L_rating-W_rating)/spread))**(-1)
        rating_change = round(k*(actual_win_ratio-expected_win_ratio))
        
        # Update ratings (check for singles)
        game_ratings[game.WO]+= rating_change
        game_ratings[game.LO]-= rating_change
        game_ratings[game.WD]+= rating_change 
        game_ratings[game.LD]-= rating_change
        game_ratings['VOID'] = 1000 #VOID rating never changes
        ratings.loc[idx] = game_ratings
        
    
    
    # Find active players in last month
    last_month_games = gamelog[gamelog.Date>(stop_date-timedelta(30))]
    active_players = np.unique(last_month_games[['WO','WD','LO','LD']])
    
    # Find change in rating and ranking for active players
    trun_ratings = ratings[gamelog.Date<(stop_date-timedelta(7))]
    cur_ratings = pd.Series({name:ratings[name].iloc[-1] for name in active_players})
    prev_ratings = pd.Series({name:trun_ratings[name].iloc[-1] for name in active_players})
    diff_ratings = cur_ratings - prev_ratings
    diff_rankings = cur_ratings.rank(method='min') - prev_ratings.rank(method='min')
    
    # Write weekly results to csv
    week_results_dict = {'Name':cur_ratings.index,
                         'Rank':cur_ratings.rank(ascending=False, method='min'),
                         'Rank Change':diff_rankings,
                         'Rating':cur_ratings.values,
                         'Rating Change':diff_ratings}
    week_results_df = pd.DataFrame(week_results_dict)
    week_results_df.sort_values('Rank', inplace=True)
    week_results_df.to_csv('week_results.csv', index=False)
    return

## Further analysis
def compute_stats(gamelog, players, game_limit=5):
    entries = ['Games','Wins','Losses','OffWins','OffLosses','DefWins','DefLosses',
             'WinPct','LossPct','OffWinPct','DefWinPct','PointsFor','PointsAgainst',
             'PointsDiff','PointMargin']
    
    stats = pd.DataFrame(index = entries)
    
    # If no players specified, return empty df
    if len(players)==0:
        return stats
    
    for player in players:
        offwins, defwins, offlosses, deflosses, *_ = (gamelog==player).sum()
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
    
#stats = compute_stats(gamelog, active_players)
#stats.to_csv('overall_stats.csv')
#stats = get_all_matchups(gamelog, 'andy', players)










