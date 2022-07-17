# -*- coding: utf-8 -*-
"""
Created on Fri Jul 15 22:46:01 2022

@author: afish
"""

from ELO import ELO
import pandas as pd
import numpy as np
import scipy.optimize


date = '07/15/2022'
gamelog_file = 'Game Log.csv'
elo = ELO(gamelog_file, datestr=date, k=100, spread=200)
elo.simulate(single_rating=True)
gl = elo.get_par()

gl.par.hist(alpha=.2, color='k')
gl[gl.Color=='r'].par.hist(alpha=.2, color='r')
gl[gl.Color=='b'].par.hist(alpha=.2, color='b')








# =============================================================================
# # Construct stats by color
# gl = elo.gamelog
# blue_games = gl[gl.Color=='b']
# red_games = gl[gl.Color=='r']
# stats_all = elo.parse_stats(gl)
# stats_blue = elo.parse_stats(blue_games)
# stats_red = elo.parse_stats(red_games)
# 
# stats = pd.concat([stats_all, stats_blue, stats_red], keys=['all','blue','red'])
# stats.to_csv('stats.csv')
# =============================================================================
