# -*- coding: utf-8 -*-
"""
Created on Thu Dec 29 13:08:50 2022

@author: afisher
"""

import re
import Blocks
import ELO
import pandas as pd

# Determines which channels each function can be used in
# 'C' is start of group channels. 'D' is start of direct message channels.
function_scopes = {
    'newgame':['C'],
    'newplayer':['C'],
    'delete':['C'],
    'ratings':['D'],
    'matchup':['D'],
    'tenzeros':['D'],
    'plot':['D'],
    'stats':['D'],
    'last':['D','C'],
    'help':['D','C']
}
    

def function_help(argument):
    post_object = {
        'text':( 
            'The following are possible commands:\n'
            '\tfoosball channel: newgame(WO, WD, LO, LD, score, winner_color)\n'
            '\tfoosball channel: newplayer(new_player_name)\n'
            '\tfoosball channel: delete(index)\n'
            '\tfoosbot DM: ratings()\n'
            '\tfoosbot DM: matchup(team1_players;team2_players)\n'
            '\tfoosbot DM: tenzeros(optional_player_name)\n'
            '\tfoosbot DM: plot(n_months, player1, player2,...)\n'
            '\tfoosbot DM: stats(player)\n'
            '\tfoosball channel and foosbot DM: last(num_games)\n'
            '\tfoosball channel and foosbot DM: help()\n'
            'For more detailed info, right click foosbot app -> View app details '
            '-> Configuration -> Description'
        )
    }
    return post_object

def parse_slackbot_call(text):
    leftpar = text.find('(')
    rightpar = text.find(')')
    function = text[:leftpar].strip().lower()
    argument = text[leftpar+1:rightpar].strip().lower()
    return function, argument

def submit_game(WO, WD, LO, LD, score, date, color):
    newgame = pd.Series( 
        data = [WO, WD, LO, LD, int(score), date, color[0]],
        index = ['WO','WD','LO','LD','Score','Date','Color']
    )
    rating_change = ELO.append_game(newgame)
    description = (
        'Added game to database\n'
        f'{WO} and {WD} beat {LO} and {LD} 10-{score} with {color}\n'
    )
    if rating_change>=0:
        description += f'Winners gain {round(rating_change,1)} rating'
    else:
        description += f'Losers gain {round(-rating_change,1)} rating'
        
    post_object = {'text':description}
    return post_object
    
def function_plot(argument):
    args = [arg.strip().lower() for arg in argument.split(',')]
    if not args[0].isdigit():
        return {'text':(
            'First argument much specify number of months to plot. For example:\n'
            '\tplot(3, player1)\n'
            '\tplot(5, player1, player2, player3')
        }
    
    if len(args)<2:
        return {'text':(
            'You need to supply at least two arguments. Number of months'
            ' and at least one player. For example:\n'
            '\tplot(3, player1)\n'
            '\tplot(5, player1, player2, player3')
        }
    n_months = int(args[0])
    players = args[1:]
    valid_players = ELO.get_player_list()
    if not set(players).issubset(set(valid_players)):
        return {'text':('Not all of the players can be recognized')}
    
    
    ELO.plot_ratings(n_months, players, 'rating_plot.png')
    post_object = {
        'image_file':'rating_plot.png',
        'text':'Ratings over Time'
    }
    return post_object


def function_newgame(argument):
    # Separate, strip, and convert to lowercase
    args = [arg.strip().lower() for arg in argument.split(',')]
    
    # Get list of players
    players = ELO.get_player_list()
    
    # Define initial menu selections
    initial_selections = [None]*6
    if len(args)>=4:
        for j in range(4):
            player = args[j]
            if player in players:
                initial_selections[j] = Blocks.option_object(player)
        if len(args)>4:
            if args[4].isalpha():
                color, score_str = args[4].lower(), args[5]
            else:
                color, score_str = args[5].lower(), args[4]
            if color in ['red','blue']:
                initial_selections[4] = Blocks.option_object(color)
            if score_str.isnumeric() and int(score_str) in range(10):
                initial_selections[5] = Blocks.option_object(score_str)

    # Build menu blocks
    blocks = [
        Blocks.static_select('WO_id', 'Winner Offense', players,
                                  initial_option = initial_selections[0]),
        Blocks.static_select('WD_id', 'Winner Defense', players,
                                  initial_option = initial_selections[1]),
        Blocks.static_select('LO_id', 'Loser Offense', players,
                                  initial_option = initial_selections[2]),
        Blocks.static_select('LD_id', 'Loser Defense', players,
                                  initial_option = initial_selections[3]),
        Blocks.static_select('color_id', 'Winner Color', ['red','blue'],
                                  initial_option = initial_selections[4]),
        Blocks.static_select('score_id', 'Score', range(10),
                                  initial_option = initial_selections[5]),
        Blocks.actions( 
            Blocks.button('cancel_id','','Cancel', action_id='cancel_message')['accessory'],
            Blocks.button('submit_id','','Add to Database', action_id='submit_game-action')['accessory']
        )
    ] 
    post_object = { 
        'text':'Confirm game information',
        'blocks':blocks
    }
    return post_object
        
def function_newplayer(argument):
    players = ELO.get_player_list()
    player = argument.strip().lower()
    if player in players:
        post_object = {'text':f'Player {player} already exists'}
    else:
        if player.isalpha():
            ELO.add_player(player)
            post_object = {'text':f'Player {player} added successfully'}
        else:
            post_object = {'text':'Player name can only contain letters.'}
    return post_object
        
def function_ratings(argument):
    filter_by = argument if argument in ['offense','defense','total'] else 'total'
    ratings = ELO.get_current_ratings(filter_by)
    post_object = { 
        'blocks':[Blocks.markdown(ratings.to_markdown())],
        'text':'Error showing blocks'
    }
    return post_object

def function_tenzeros(argument):
    players = ELO.get_player_list()
    if argument in players:
        tenzeros = ELO.get_tenzeros(argument)
    else:
        tenzeros = ELO.get_tenzeros()
        
    post_object = { 
        'blocks':[Blocks.markdown(tenzeros.to_markdown())],
        'text':'Error showing blocks'
    }
    return post_object
    
def function_stats(argument):
    players = ELO.get_player_list()
    if argument in players:
        stats = ELO.get_player_stats(argument)
        post_object = { 
            'blocks':[
                Blocks.markdown(stats['all time'].to_markdown()),
                Blocks.markdown(stats.stack().swaplevel().loc['all'].to_markdown())
            ],
            'text':'Error showing blocks'
        }
    else:
        post_object = {'text':'Argument is not a valid player'}
    return post_object
        
def function_last(argument):
    if not argument.isdigit():
        post_object = {'text':'Argument must be an integer'}
    else:
        games = ELO.get_last_games(int(argument))
        post_object = { 
            'blocks':[Blocks.markdown(games.to_markdown())],
            'text':'Error showing blocks'
        }
    return post_object
    

def function_matchup(argument):
    # Must contain semicolon
    if argument.find(';')==-1:
        return {'text': (
            'Must use a semicolon to separate teams. Here are examples\n'
            '\tmatchup(player1, player2; player3, player4)\n'
            '\tmatchup(player1; player2)\n'
            '\tmatchup(player1;)\n'
        )}
            
    team1_str, team2_str = argument.split(';')
    team1 = [player.strip() for player in team1_str.split(',')]
    if team2_str=='':
        team2 = []
    else:
        team2 = [player.strip() for player in team2_str.split(',')]
    players = ELO.get_player_list()
    
    if not set(team1).union(set(team2)).issubset(set(players)):
        return {'text':'There is an unrecognized player'}
    if len(set(team1).intersection(set(team2)))>0:
        return {'text':'A player cannot be on both teams'}
    if len(team1)>len(set(team1)) or len(team1)>2:
        return {'text':'Duplicate or too many players on team1'}
    if len(team2)>len(set(team2)) or len(team2)>2:
        return {'text':'Duplicate or too many players on team2'}
    
    matchups = ELO.get_matchups(team1, team2)
    post_object = { 
        'blocks':[Blocks.markdown(matchups.to_markdown())],
        'text':'Error showing blocks'
    }
    return post_object
    
def function_delete(argument):
    if not argument.isdigit():
        return {'text':(
            'Argument must be index of game to delete.\n'
            'Use last(n_games) to view game indices.'
        )}

    index = int(argument)
    game = ELO.get_game_by_index(index)
    WO, WD, LO, LD, score, date, c = game.values
    color = 'red' if c=='r' else 'blue'
    
    description = (
        f'Delete game {argument}?\n'
        f'{WO} and {WD} beat {LO} and {LD} 10-{score} with {color} on {date}'
    )
        
        
    # Build blocks
    blocks = [
        Blocks.static_select('idx_id', description, [index], 
                             initial_option =  Blocks.option_object(index)),
        Blocks.actions( 
            Blocks.button('cancel_id','','Cancel', action_id='cancel_message')['accessory'],
            Blocks.button('submit_id','','Delete', action_id='delete_game-action')['accessory']
        )
    ]
    post_object = { 
        'blocks':blocks,
        'text':'Error showing blocks'
    }
    return post_object
    















    