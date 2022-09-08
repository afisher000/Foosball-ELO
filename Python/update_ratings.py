# -*- coding: utf-8 -*-
"""
Created on Fri Jul 15 22:46:01 2022

@author: afish
"""

from ELO import ELO
import pandas as pd
import numpy as np
import scipy.optimize
import matplotlib.pyplot as plt
plt.close('all')

date = '9/6/2022'
gamelog_file = 'Game Log.csv'
elo = ELO(gamelog_file, datestr=date, k=64, spread=200)
elo.simulate(single_rating=False)
elo.print_results()
gl = elo.get_par()


red = gl[gl.Color=='r']
blue = gl[gl.Color=='b']

print('Points Gained by Winners')
print(f'Blue: Mean={blue.points_gained.mean():.2f}, Std={blue.points_gained.std():.2f}')
print(f'Red: Mean={red.points_gained.mean():.2f}, Std={red.points_gained.std():.2f}')

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
