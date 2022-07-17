# -*- coding: utf-8 -*-
"""
Created on Sat May 14 12:26:06 2022

@author: afish
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import operator as op



class ELO():
    def __init__(self, gamelog_file, k=64, spread=200, datestr=None):
        
        if datestr is None:
            self.data = datetime.today()
        else:
            self.date = datetime.strptime(datestr, '%m/%d/%Y')
            
        self.gamelog_file = gamelog_file
        self.k = k
        self.spread = spread
        self.players = np.array([
            'atharva',  'andy',     'alex',     'sophie',   'pietro',
            'lucy',     'paul',     'lawler',   'max',      'andonian',
            'eric',     'jake',     'obed',     'pratik',   'fabio',
            'stefano',  'david',
            'VOID'])
        
        self.check_gamelog()
    

    def check_gamelog(self):
        ''' Checks gamelog file to make sure there are no name errors or 
        score errors in the data.'''
        gamelog = pd.read_csv(self.gamelog_file)
        
        # Check gamelog names are correct
        name_errors = (~gamelog[['WO','WD','LO','LD']].isin(self.players)).any(axis=1)
        if name_errors.sum()>0:
            print(gamelog.loc[name_errors])
            raise Exception('These rows have unidentified players.\n')
            
        # Check gamelog scores are correct
        score_errors = ~gamelog.Score.isin(range(10))
        if score_errors.sum()>0:
            print(gamelog.loc[score_errors])
            raise Exception('These rows have an incorrect score...\n')
        return
        
    def get_par(self):
        # Add wins-above-replacement column to gamelog
        r = self.get_ratings()
        gl = self.gamelog.copy()
        W_rating = r[gl.WO+'_off'].values/2 + r[gl.WD+'_def'].values/2
        L_rating = r[gl.LO+'_off'].values/2 + r[gl.LD+'_def'].values/2
        actual_win_ratio = 10/(gl.Score.values+10)
        expected_win_ratio = (1+10**((L_rating-W_rating)/self.spread))**(-1)
        gl['par'] = self.k * (actual_win_ratio - expected_win_ratio)
        return gl
        
        
        
        
    def simulate(self, k=64, spread=200, single_rating=False):
        # 1000 Initial Rating for offense and defense
        rating_hist = pd.DataFrame(np.zeros((1,len(self.players))), columns=self.players)
        rating_hist = rating_hist.join(rating_hist, lsuffix='_off', rsuffix='_def')
        
        # Read gamelog
        gamelog = pd.read_csv(self.gamelog_file)
        gamelog.Date = gamelog.Date.map(lambda x: datetime.strptime(x, '%m/%d/%Y'))
        
        # Drop singles games
        singles = (gamelog.WO==gamelog.WD) | (gamelog.LO==gamelog.LD)
        gamelog = gamelog[~singles].reset_index(drop=True) 
            
        # Update Ratings
        for idx, game in gamelog.iterrows():
            if idx==0:
                game_ratings = pd.Series(1000*np.ones(len(rating_hist.columns)), index=rating_hist.columns)
            else:
                game_ratings = rating_hist.loc[idx-1].copy()
            
            # Compute actual and expected point-win ratios
            W_rating = game_ratings[game.WO+'_off']/2 + game_ratings[game.WD+'_def']/2
            L_rating = game_ratings[game.LO+'_off']/2 + game_ratings[game.LD+'_def']/2
            actual_win_ratio = 10/(game.Score+10)
            expected_win_ratio = (1+10**((L_rating-W_rating)/self.spread))**(-1)
            rating_change = round(self.k*(actual_win_ratio-expected_win_ratio))
            
            # Update ratings (check for singles)
            game_ratings[game.WO+'_off']+= rating_change
            game_ratings[game.LO+'_off']-= rating_change
            game_ratings[game.WD+'_def']+= rating_change 
            game_ratings[game.LD+'_def']-= rating_change
            game_ratings['VOID'] = 1000 #VOID rating never changes
            
            # Change other rating as well if using single_rating
            if single_rating:
                game_ratings[game.WO+'_def']+= rating_change
                game_ratings[game.LO+'_def']-= rating_change
                game_ratings[game.WD+'_off']+= rating_change 
                game_ratings[game.LD+'_off']-= rating_change
                
            rating_hist.loc[idx] = game_ratings
            
        self.rating_hist = rating_hist    
        self.gamelog = gamelog
        
        # Find active players in last month
        last_month_games = gamelog[gamelog.Date>(self.date-timedelta(30))]
        self.active_players = np.unique(last_month_games[['WO','WD','LO','LD']])
    
        # Find change in rating and ranking for active players
        self.prev_r = rating_hist[gamelog.Date<(self.date-timedelta(7))].iloc[-1]
        self.cur_r = rating_hist[gamelog.Date<=self.date].iloc[-1]
        
        return
    
    def get_ratings(self):
        if not hasattr(self, 'cur_r'):
            print('You have to run self.simulate() before calling results.')
            return
        return self.cur_r

    def print_results(self):
        if not hasattr(self, 'cur_r'):
            print('You have to run self.simulate() before you can print results.')
            return
        
        # Make ratings dataframe
        r = pd.DataFrame()
        r.index = self.active_players
        r['cur_offense'] = [self.cur_r[name+'_off'] for name in self.active_players]
        r['cur_defense'] = [self.cur_r[name+'_def'] for name in self.active_players]
        r['cur_total'] = r.cur_offense/2 + r.cur_defense/2
        r['prev_offense'] = [self.prev_r[name+'_off'] for name in self.active_players]
        r['prev_defense'] = [self.prev_r[name+'_def'] for name in self.active_players]
        r['prev_total'] = r.prev_offense/2 + r.prev_defense/2
        r['offense_rating_change'] = r.cur_offense - r.prev_offense
        r['defense_rating_change'] = r.cur_defense - r.prev_defense
        r['total_rating_change'] = r.cur_total - r.prev_total
        r['cur_rank'] = r.cur_total.rank(ascending=False, method='min')
        r['prev_rank'] = r.prev_total.rank(ascending=False, method='min')
        r['rank_change'] = r.cur_rank - r.prev_rank
        r.sort_values(by='cur_rank', inplace=True)
        r = r.astype(int)
        
        # Write to csv file
        r['rating_str'] = '(' + r.cur_offense.astype(str) +',' \
            + r.cur_defense.astype(str) \
            + ') ' + r.cur_total.astype(str)     
        r['rating_change_str']  = '(' + r.offense_rating_change.astype(str) +',' \
            + r.defense_rating_change.astype(str) \
            + ') ' + r.total_rating_change.astype(str)                            
        r['name'] = r.index
        
        csv_headers = ['Name','Rank','Rank Change','Rating (Off,Def)','Rating Change']
        r_headers = ['name', 'cur_rank', 'rank_change', 'rating_str', 'rating_change_str']
        r[r_headers].rename(columns=dict(zip(r_headers, csv_headers))).to_csv('week_results.csv', index=False)
        return

    def parse_stats(self, gamelog, min_games=10):
        players = np.unique(gamelog[['WO','WD','LO','LD']])
        stats = pd.DataFrame(index=players)
        stats['win_off'] = gamelog.WO.value_counts()
        stats['win_def'] = gamelog.WD.value_counts()
        stats['loss_off'] = gamelog.LO.value_counts()
        stats['loss_def'] = gamelog.LD.value_counts()
        stats = stats.fillna(0)
        stats['win'] = stats.win_off + stats.win_def
        stats['loss'] = stats.loss_off + stats.loss_def
        stats['games'] = stats.win + stats.loss
        stats['win_pct'] = stats.win/stats.games*100
        stats['off_win_pct'] = stats.win_off/(stats.win_off+stats.loss_off)*100
        stats['def_win_pct'] = stats.win_def/(stats.win_def+stats.loss_def)*100
        
        for player in stats.index:
            stats.loc[player,'Pfor'] = stats.loc[player,'win']*10 + \
                gamelog.Score[(gamelog.LO==player)|(gamelog.LD==player)].sum().astype(int)
            stats.loc[player,'Pagainst'] = stats.loc[player,'loss']*10 + \
                gamelog.Score[(gamelog.WO==player)|(gamelog.WD==player)].sum().astype(int)
                
        stats = stats.fillna(-1).astype(int)
        stats['Pmargin'] = (stats.Pfor-stats.Pagainst) / stats.games
        
        # Drop 'VOID' placeholder and infrequent players
        if 'VOID' in stats.index:
            stats = stats.drop('VOID')
        stats = stats[stats.games>=min_games]
        return stats







