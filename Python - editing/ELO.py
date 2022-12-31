# -*- coding: utf-8 -*-
"""
Created on Sat May 14 12:26:06 2022

@author: afish
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import operator as op
from datetime import datetime, timedelta
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import os


gamelog_database = 'gamelog_db.csv'
ratings_database = 'ratings_db.csv'


def plot_ratings(n_months, players, file):
    gl_db = pd.read_csv(gamelog_database)
    idx = get_index_from_months(gl_db=gl_db, months=n_months)
    dates = gl_db.Date.apply(lambda x: datetime.strptime(x, '%m/%d/%Y'))
    r_db = pd.read_csv(ratings_database, header=[0,1])
    
    colors = mcolors.TABLEAU_COLORS.values()
    plt.ioff() #ensure figure does not display
    fig, ax = plt.subplots()
    for color, player in zip(colors,players):
        ax.plot(dates, r_db[(player, 'offense')], linestyle='dashed', c=color, label=player+'_off')
        ax.plot(dates, r_db[(player, 'defense')], linestyle='dotted', c = color, label=player+'_def')
    ax.legend()
    ax.set_ylabel('Rating')
    ax.set_xlabel('Year-Month')
    plt.ion()
    plt.savefig(file)
    return

    
def delete_game_by_index(idx):
    # Remove game from database
    gl_db = pd.read_csv(gamelog_database)
    gl_db = gl_db.drop(idx)
    gl_db.to_csv(gamelog_database, index=False)
    
    # Rebuild ratings
    rebuild_rating_db()
    return

def get_game_by_index(idx):
    gl_db = pd.read_csv(gamelog_database)
    return gl_db.loc[idx]

def get_matchups(team1, team2):
    gl_db = pd.read_csv(gamelog_database)
    title = ','.join(team1) + ' vs. ' + ','.join(team2)
    
    # Keep track of win and losses by team1 vs team2
    cond_win = np.full(len(gl_db), True)
    cond_loss = np.full(len(gl_db), True)
    
    for player in team1:
        for player in team1:
            cond_win &= (gl_db==player)[['WO','WD']].any(axis=1)
            cond_loss &= (gl_db==player)[['LO','LD']].any(axis=1)
        for player in team2:
            cond_win &= (gl_db==player)[['LO','LD']].any(axis=1)
            cond_loss  &= (gl_db==player)[['WO','WD']].any(axis=1)
     
    
    # Compute statistics
    eps = 1e-4
    wins = cond_win.sum()
    losses = cond_loss.sum()
    games = wins+losses
    win_pct = 100*wins/(games+eps)
    gl_win = gl_db[cond_win]
    gl_loss = gl_db[cond_loss]
    margin = ((wins*10+gl_loss.Score.sum()) - (losses*10+gl_win.Score.sum()))/(games+eps)
    games_with_blue = (gl_win.Color=='b').sum() + (gl_loss.Color=='r').sum()
    games_with_red  = (gl_win.Color=='r').sum() + (gl_loss.Color=='b').sum()
    blue_pct = 100*games_with_blue / (games_with_blue + games_with_red + eps)

    stats = pd.DataFrame( 
        data = [games, wins, losses, win_pct, margin, blue_pct],
        index = ['games','wins','losses','win %', 'margin', 'blue %'],
        columns = [title]
    )
    stats = stats.round().astype(int)
    stats.loc['margin'] = round(margin, 1)
    return stats
        
    
    
    
def get_last_games(n_games):
    gl_db = pd.read_csv(gamelog_database)
    return gl_db.iloc[-n_games:].copy()
    
def append_game(newgame):
    # Add to gamelog
    gl_db = pd.read_csv(gamelog_database)
    gl_db.loc[len(gl_db)] = newgame
    gl_db.to_csv(gamelog_database, index=False)

    # Add to ratings
    r_db = pd.read_csv(ratings_database, header=[0,1])
    rating_change = append_to_ratings(r_db, newgame)
    r_db.to_csv(ratings_database, index=False)
    return rating_change

def append_to_ratings(r_db, game):
    idx = len(r_db)
    if idx==0:
        r_db.loc[idx] = 1000
    else:
        r_db.loc[idx] = r_db.loc[idx-1].copy()
        
    # Compute rating change
    WO_player, WD_player, LO_player, LD_player = game[['WO','WD','LO','LD']]
    W_col = [(WO_player, 'offense'), (WD_player, 'defense')]
    L_col = [(LO_player, 'offense'), (LD_player, 'defense')]
    W_rating = r_db.loc[idx, W_col].mean()
    L_rating = r_db.loc[idx, L_col].mean()
    rating_change = get_rating_change(W_rating, L_rating, game.Score)
    
    # Update ratings
    r_db.loc[idx, W_col] += rating_change
    r_db.loc[idx, L_col] -= rating_change
    return rating_change
    
    
    
def rebuild_rating_db():
    # Read in gamelog and ratings
    gl_db = pd.read_csv(gamelog_database)
    
    # Return if already up-to-date
    if os.path.exists(ratings_database):
        r_db = pd.read_csv(ratings_database, header=[0,1])
        if len(gl_db)==len(r_db):      
            return
    

    # Build ratings dataframe
    players = np.unique(gl_db[['WO','WD','LO','LD']])
    r_db = pd.DataFrame(
        columns = pd.MultiIndex.from_product([players, ['offense','defense']])
    )
    
    # Populate ratings for all games
    for _, game in gl_db.iterrows():
        append_to_ratings(r_db, game)

    # Save to file
    r_db.to_csv(ratings_database, index=False)
    
    
def get_index_from_months(gl_db=None, months=1):
    if gl_db is None:
        gl_db = pd.read_csv(gamelog_database)
    dates = gl_db.Date
    dates = dates.apply(lambda x: datetime.strptime(x, '%m/%d/%Y'))
    is_recent = dates > datetime.today() - months*timedelta(30)
    month_ago_idx = np.argmax(is_recent)
    return month_ago_idx
    
def get_player_stats(player):
    gl_db = pd.read_csv(gamelog_database)
    player_alltime = gl_db[(gl_db==player).any(axis=1)]
    month_ago_idx = get_index_from_months(gl_db)
    player_month = player_alltime.loc[month_ago_idx:].copy()
    
    def stats_by_color(gl, color=None):
        is_player = (gl==player)
        if color is not None:
            is_color = ~(is_player[['WO','WD']].any(axis=1)^(gl.Color.str.find(color)!=-1))
            totals = is_player[is_color].sum()
        else:
            totals = is_player.sum()
        games = totals.sum()
        wins = totals[['WO','WD']].sum()
        losses = games - wins
        eps = 1e-4
        win_pct = 100*wins/(games+eps)
        off_win_pct = 100*totals.WO/(totals.WO+totals.LO+eps)
        def_win_pct = 100*totals.WD/(totals.WD+totals.LD+eps)
        color_stats = pd.Series( 
            data = [games, wins, losses, win_pct, off_win_pct, def_win_pct],
            index = ['games','wins','losses','win %','off win %','def win %']
        )
        return color_stats.round().astype(int)

    stats = pd.DataFrame(
        data = np.vstack([ 
             stats_by_color(player_alltime),
             stats_by_color(player_alltime, 'b'),
             stats_by_color(player_alltime, 'r'),
             stats_by_color(player_month),
             stats_by_color(player_month, 'b'),
             stats_by_color(player_month, 'r'),
        ]).T,
        index = ['games','wins','losses','win %','off win %','def win %'],
        columns = pd.MultiIndex.from_product([
                ['all time','last month'],
                ['all','blue','red']
        ])
    )
    return stats
    
    
    
def get_tenzeros(player=None):
    gl_db = pd.read_csv(gamelog_database)
    tenzeros = gl_db[gl_db.Score==0]
    
    # Optionally filter to include only player tenzeros
    if player is not None:
        tenzeros = tenzeros[(tenzeros==player).any(axis=1)]
    return tenzeros
    
    
def get_current_ratings(filter_by=None):
    # Read last line of ratings database, reshape
    r_db = pd.read_csv(ratings_database, header=[0,1])
    current_ratings = r_db.iloc[-1,:].unstack()
    current_ratings['total'] = current_ratings.mean(axis=1)
    
    # Remove inactive players
    idx = get_index_from_months()
    is_unchanged = (r_db.iloc[-1]-r_db.iloc[idx]==0)
    recent_players = ~is_unchanged.unstack().all(axis=1)
    current_ratings = current_ratings[recent_players]
    
    # Optionally filter
    if filter_by is not None:
        current_ratings.sort_values(by=filter_by, ascending=False, inplace=True)
    
    
    # Ensure column ordering
    current_ratings = current_ratings[['offense','defense','total']]
    # Return as integers
    return current_ratings.round().astype(int)
    
    
def get_player_list():
    # Read only header of ratings database
    r_db = pd.read_csv(ratings_database, header=[0,1], nrows=1)
    player = r_db.columns.unique(level=0).to_list()
    return player

def get_rating_change(W_rating, L_rating, score):
    k = 64
    spread = 200
    actual_win_ratio = 10/(score+10)
    expected_win_ratio = (1+10**((L_rating-W_rating)/spread))**(-1)
    rating_change = k*(actual_win_ratio-expected_win_ratio)
    return rating_change
       


def add_player(new_player):
    r_db = pd.read_csv(ratings_database, header=[0,1])
    r_db[(new_player, 'offense')] = 1000
    r_db[(new_player, 'defense')] = 1000
    r_db.to_csv(ratings_database, index=False)
    return
    