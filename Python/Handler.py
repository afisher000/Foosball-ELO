# -*- coding: utf-8 -*-
"""
Created on Sun Sep  4 11:53:55 2022

@author: afish
"""
from ELO import ELO
import pandas as pd
import numpy as np
from Blocks import Blocks
import re
import datetime
import matplotlib.pyplot as plt
import pickle


elo = ELO('Game Log.csv', k=64, spread=200)
elo.simulate()
players = np.unique(elo.gamelog[['WO','WD','LO','LD']].values)
ratings = elo.get_ratings()
        
        
# TO IMPLEMENT:
    # change colorbias so that it follows a certain color, not the color of the winner (want ideal average to be 0)
    # add stats by color
    
    
class Handler():
    def __init__(self, app, SLACK_BOT_TOKEN, SLACK_BOT_USER_TOKEN):
        self.elo = ELO('Game Log.csv', k=64, spread=200)
        self.elo.simulate()
        self.players = np.unique(self.elo.gamelog[['WO','WD','LO','LD']].values)
        self.ratings = self.elo.get_ratings()
        self.Blocks = Blocks()
        self.SLACK_BOT_USER_TOKEN = SLACK_BOT_USER_TOKEN
        self.SLACK_BOT_TOKEN = SLACK_BOT_TOKEN
        self.app = app
        
        self.possible_commands = '''The following are possible commands:
        foosball channel: newgame(WO, WD, LO, LD, score, winner_color)
        foosball channel: newplayer(new_player_name)
        foosbot DM: ratings()
        foosbot DM: matchup(team1_players;team2_players)
        foosbot DM: tenzeros(optional_player_name)
        foosbot DM: colorbias()
        foosbot DM: last(num_games)
        foosball channel and foosbot DM: help()
        For more detailed info, right click foosbot app -> View app details ->
        Configuration -> Description'''

    def parse_call(self, text, say):
        regex = re.compile('^([\w\s]*)\(([^\)]*)\)$')
        try:
            groups = regex.search(text).groups()
            keyword, item = [group.strip().lower() for group in groups]
        except:
            keyword = None
            item = None
        
        return keyword, item

    def find_matchups(self, channel, item):
        # Parse player inputs
        error = {'state':False, 'message':''}
        team_strs = item.split(';')
        team1_list = [player.strip() for player in team_strs[0].split(',')]
        team1_set = set(team1_list)
        
        if len(team_strs)>1:
            team2_list = [player.strip() for player in team_strs[1].split(',')]
            team2_set = set(team2_list)
        else:
            team2_list = []
            team2_set = {}

        if not team1_set.union(team2_set).issubset(set(players)):
            error = {'state':True, 'message':'Unrecognized player'}
            
        if len(team1_set.intersection(team2_set))>0:
            error = {'state':True, 'message':'Player exists on both teams'}
            
        if len(team1_list)>len(team1_set) or len(team1_list)>2:
            error = {'state':True, 'message':'Duplicate or too many players on team1'}
        
        if len(team2_list)>len(team2_set) or len(team2_list)>2:
            error = {'state':True, 'message':'Duplicate or too many players on team2'}
            
        if error['state']:
            self.app.client.chat_postMessage(token=self.SLACK_BOT_USER_TOKEN,
                channel=channel,
                text=error['message'])  
            return
        
        # Find games where team1 wins and team1 loses
        gl = self.elo.gamelog
        cond_win = gl.any(axis=1) #start with all trues
        cond_loss = gl.any(axis=1) 
        for player in team1_list:
            cond_win &= (gl==player)[['WO','WD']].any(axis=1)
            cond_loss &= (gl==player)[['LO','LD']].any(axis=1)
        for player in team2_list:
            cond_win &= (gl==player)[['LO','LD']].any(axis=1)
            cond_loss  &= (gl==player)[['WO','WD']].any(axis=1)
        
        
        column_name = ','.join(team1_list) + ' vs. ' + ','.join(team2_list)
        wins = cond_win.sum().round()
        losses = cond_loss.sum().round()
        games = wins+losses
        gl_loss = gl[cond_loss]
        gl_win = gl[cond_win]
        
        if games==0:
            self.app.client.chat_postMessage(token=self.SLACK_BOT_USER_TOKEN,
                channel=channel,
                text='No results')
            return
        
        data = {'Games':games,
                'Wins':wins,
                'Losses':losses,
                'Win_pct':round(wins/games*100, 2),
                'Margin': round((wins*10+gl_loss.Score.sum() - losses*10 - gl_win.Score.sum())/games, 2),
                'Blue_pct': round(((gl_win.Color=='b').sum()+(gl_loss.Color=='r').sum())/(len(gl_win.Color.dropna())+len(gl_loss.Color.dropna())), 2)
                }
        statistics = pd.DataFrame(data.values(), index=data.keys(), columns=[column_name])
        
        # print table
        self.app.client.chat_postMessage(token=self.SLACK_BOT_USER_TOKEN,
            channel=channel,
            text='Matchup Statistics',
            blocks = [self.Blocks.markdown(statistics.to_markdown())])
        return
    
    def new_game(self, channel, item=''):
        player_select = [None]*4
        color_select = score_select = None
        
        args = item.split(',')
        if len(args)>=4:
            args = item.split(',')
            for j, arg in enumerate(args[:4]):
                player = arg.strip().lower()
                if player in self.players:
                    player_select[j] = self.Blocks.option_object(player)
            
        if len(args)>=5:
            if args[4].strip() in list(map(str, range(10))):
                score_select = self.Blocks.option_object(args[4].strip())
                
        if len(args)>=6:
            color = args[5].strip().lower()
            if color in ['red','blue']:
                color_select = self.Blocks.option_object(color)
        
        
        blocks = [
            self.Blocks.static_select('WO_id', 'Winner Offense', self.players,
                                      initial_option = player_select[0]),
            self.Blocks.static_select('WD_id', 'Winner Defense', self.players,
                                      initial_option = player_select[1]),
            self.Blocks.static_select('LO_id', 'Loser Offense', self.players,
                                      initial_option = player_select[2]),
            self.Blocks.static_select('LD_id', 'Loser Defense', self.players,
                                      initial_option = player_select[3]),
            self.Blocks.static_select('color_id', 'Winner Color', ['red','blue'],
                                      initial_option = color_select),
            self.Blocks.static_select('score_id', 'Score', range(10),
                                      initial_option = score_select),
            self.Blocks.actions(self.Blocks.button('cancel_id','','Cancel', action_id='cancel_message')['accessory'],
                                self.Blocks.button('submit_id','','Add to Database', action_id='submit_game-action')['accessory'])
            ] 

        self.app.client.chat_postMessage(
            token=self.SLACK_BOT_USER_TOKEN,
            channel=channel,
            text = 'Add game information',
            blocks = blocks
            )
        return

    def player_stats(self, player):
        # Games, offensive win pct, defensive win pct, color pct
        gl_all = self.elo.gamelog[(self.elo.gamelog==player).any(axis=1)]
        month_ago = datetime.datetime.today() - datetime.timedelta(30)
        gl_month = gl_all[gl_all.Date>month_ago].copy()
        
        def stats_from_subtable(gl):
            stats = {}
            counts = (gl==player).sum()
            
            win_colors = gl[(player==gl[['WO','WD']]).any(axis=1)].Color.dropna().value_counts()
            lose_colors = gl[(player==gl[['LO','LD']]).any(axis=1)].Color.dropna().value_counts()
            if not hasattr(win_colors, 'b'):
                win_colors['b']=0
            if not hasattr(lose_colors, 'r'):
                lose_colors['r']=0
                
            games = counts.sum()
            off_games = counts.WO + counts.LO
            def_games = counts.WD + counts.LD
            
            stats['games'] = games
            if off_games==0:
                stats['off_win_pct'] = -1
            else:
                stats['off_win_pct'] = round(counts.WO/off_games*100)
                
            if def_games==0:
                stats['def_win_pct']  = -1
            else:
                stats['def_win_pct']  = round(counts.WD/def_games*100) 
            stats['blue_pct']  = round((win_colors.b + lose_colors.r) / (win_colors.sum() + lose_colors.sum())*100)
            return stats

        
        return pd.DataFrame({'Last Month':stats_from_subtable(gl_month),
                             'All Time':stats_from_subtable(gl_all)})

    def update_ratings(self, WO, WD, LO, LD, score):
        # Compute update ratings
        W_rating = self.ratings[WO+'_off']/2 + self.ratings[WD+'_def']/2
        L_rating = self.ratings[LO+'_off']/2 + self.ratings[LD+'_def']/2
        actual_win_ratio = 10/(int(score)+10)
        expected_win_ratio = (1+10**((L_rating-W_rating)/self.elo.spread))**(-1)
        rating_change = self.elo.k * (actual_win_ratio - expected_win_ratio)

        
        self.ratings[WO+'_off'] += rating_change
        self.ratings[WD+'_def'] += rating_change
        self.ratings[LO+'_off'] -= rating_change
        self.ratings[LD+'_def'] -= rating_change
        return rating_change
        

    def update_gamelog(self, WO, WD, LO, LD, score, color):
        # Add to gamelog and save
        self.elo.gamelog.loc[len(self.elo.gamelog)] = [WO, WD, LO, LD, int(score), 
                                                       datetime.datetime.today(), color[0]]
        temp = self.elo.gamelog.copy()
        temp.Date = temp.Date.map(lambda x: x.strftime('%m/%d/%Y'))
        temp.to_csv('Game Log.csv', index=False)
        
        
    def display_ratings(self, channel):
        cutoff_date = datetime.datetime.today() - datetime.timedelta(30)
        cur_players = np.unique(self.elo.gamelog[self.elo.gamelog.Date>cutoff_date]
                                [['WO','WD','LO','LD']])
        
        rating_table = pd.DataFrame(index=cur_players)
        rating_table['Offense'] = self.ratings[cur_players+'_off'].values
        rating_table['Defense'] = self.ratings[cur_players+'_def'].values
        rating_table['Total'] = rating_table.Offense/2 + rating_table.Defense/2
        rating_table.sort_values(by='Total', ascending=False, inplace=True)
        rating_table[['Offense','Defense','Total']] = rating_table[['Offense','Defense','Total']].applymap(lambda x: f'{x:6.0f}')

        self.app.client.chat_postMessage(token=self.SLACK_BOT_USER_TOKEN,
                                    channel=channel,
                                    text='Ratings',
                                    blocks = [self.Blocks.markdown(rating_table.to_markdown())])
            
        
    def handle_cancellation(self, ack, body, logger):
        ack()
        ts = body['message']['ts']
        channel_id = body['channel']['id']
        self.app.client.chat_delete(token=self.SLACK_BOT_USER_TOKEN,
                                   channel=channel_id, 
                                   ts=ts,
                                   blocks=None)
        return
        
        
        
    def handle_game_submission(self, ack, body, logger):
        ack()
        ts = body['message']['ts']
        channel_id = body['channel']['id']
        
        # Read selections
        try:
            WO = body['state']['values']['WO_id']['static_select-action']['selected_option']['value']
            WD = body['state']['values']['WD_id']['static_select-action']['selected_option']['value']
            LO = body['state']['values']['LO_id']['static_select-action']['selected_option']['value']
            LD = body['state']['values']['LD_id']['static_select-action']['selected_option']['value']
            color = body['state']['values']['color_id']['static_select-action']['selected_option']['value']
            score = body['state']['values']['score_id']['static_select-action']['selected_option']['value']
        except:
            self.app.client.chat_postMessage(token=self.SLACK_BOT_USER_TOKEN, 
                                             channel=channel_id,
                                             text='Selection incomplete...')
            return
        
        if len(np.unique([WO, WD, LO, LD]))<4:
            self.app.client.chat_postMessage(token=self.SLACK_BOT_USER_TOKEN, 
                                        channel=channel_id,
                                        text='Duplicate player...')
            return
            
        # Update gamelog and ratings
        self.update_gamelog(WO, WD, LO, LD, score, color)
        rating_change = self.update_ratings(WO, WD, LO, LD, score)
        
        if rating_change>0:
            rating_message = f'Added game to database.\n{WO} and {WD} beat {LO} and {LD} 10-{score} with {color}\nWinners gain {rating_change:.1f} rating'
        else:
            rating_message = f'Added game to database.\n{WO} and {WD} beat {LO} and {LD} 10-{score} with {color}\nLosers gain {-rating_change:.1f} rating'
            
            
        
        # Update chat
        self.app.client.chat_delete(token=self.SLACK_BOT_USER_TOKEN,
                                   channel=channel_id, 
                                   ts=ts,
                                   blocks=None)
        self.app.client.chat_postMessage(token=self.SLACK_BOT_USER_TOKEN, 
                                        channel=channel_id,
                                        text=rating_message)
        logger.info(body)


    def handle_message_events(self, event, say, ack):
        ack()
        foosball_channel = 'C042YTYSDJ5'
        andy_user = 'W01A1T44K2B'
        
        # if event['user'] != andy_user:
        #     print('Not Andrew posting, in testing mode...')
        #     return
        
        if 'text' not in event.keys():
            print('No "text" attribute in event object')
            return
        
        keyword, item = self.parse_call(event['text'], say)
        

        if event['channel']==foosball_channel:
            # new game
            if keyword=='newgame':
                self.new_game(event['channel'], item)
                
            elif keyword=='newplayer':
                self.players = np.append(self.players, item)
                self.ratings[item+'_def'] = 1000
                self.ratings[item+'_off'] = 1000
                say(token=self.SLACK_BOT_USER_TOKEN, text=f'Added new player "{item}"')
            elif keyword=='help':
                say(token=self.SLACK_BOT_USER_TOKEN, 
                    text=self.possible_commands)
                
        elif event['channel'][0] =='D':                              
            if keyword=='ratings':
                self.display_ratings(event['channel'])
                
            elif keyword=='tenzeros':
                tenzeros = self.elo.gamelog[self.elo.gamelog.Score==0]
                if item=='' or item is None:
                    self.app.client.chat_postMessage(token=self.SLACK_BOT_USER_TOKEN,
                                channel=event['channel'],
                                text='Ten-Zero Games',
                                blocks = [self.Blocks.markdown(tenzeros.to_markdown())])
                else:
                    player_tenzeros = tenzeros[(tenzeros==item).any(axis=1)]
                    self.app.client.chat_postMessage(token=self.SLACK_BOT_USER_TOKEN,
                                channel=event['channel'],
                                text=f'Ten-Zero Games involving {item}',
                                blocks = [self.Blocks.markdown(player_tenzeros.to_markdown())])
                    
                    
            elif keyword=='stats':
                if item in self.players:
                    self.app.client.chat_postMessage(token=self.SLACK_BOT_USER_TOKEN,
                                channel=event['channel'],
                                text=f'Stats for {item}',
                                blocks = [self.Blocks.markdown(self.player_stats(item).to_markdown())])
                
            elif keyword=='colorbias':
                gl = elo.get_par().dropna() #adds 'points_gained' column
                plt.ioff() #ensure figure does not display
                gl.plot.scatter(x='Date',y='points_gained', c='Color').get_figure().savefig('colorbias.png')
                plt.ion()
                
                blue_dist = gl[gl.Color=='b'].points_gained.agg(['mean','std'])
                red_dist = gl[gl.Color=='r'].points_gained.agg(['mean','std'])
            
                
                
                message_text = f"Mean and Std: Blue = ({blue_dist['mean']:.1f}, {blue_dist['std']:.1f}), Red = ({red_dist['mean']:.1f}, {red_dist['std']:.1f})"
                self.app.client.files_upload(token=self.SLACK_BOT_USER_TOKEN,
                                             file='colorbias.png',
                                             channels=event['channel'], 
                                             initial_comment = message_text)
                
            elif keyword=='matchup':
                self.find_matchups(event['channel'], item)
                
            elif keyword=='last':
                if item.isdigit():
                    self.app.client.chat_postMessage(token=self.SLACK_BOT_USER_TOKEN,
                                    channel=event['channel'],
                                    text=f'Last {int(item)} entries',
                                    blocks = [self.Blocks.markdown(self.elo.gamelog.iloc[-int(item):].to_markdown())])
                else:
                    self.app.client.chat_postMessage(token=self.SLACK_BOT_USER_TOKEN,
                                    channel=event['channel'],
                                    text='Argument must be an integer')
            elif keyword=='help':
                say(token=self.SLACK_BOT_USER_TOKEN, 
                    text=self.possible_commands)


            
            
