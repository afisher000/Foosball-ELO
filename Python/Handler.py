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


# TO IMPLEMENT:
    # Reformat menus, put players on one line
    
    # Include cancel buttons for messages (help keep channel clean)
    
    # colorbias()
        # return stats for different colors
        # image of distributions along with mean and std?
    
    # stats(player)
        # Give stats for all time and last month
        # Games, offensive win pct, defensive win pct, color pct
        
    # matchup(p1, p2, q1, q2)
        # Find stats on games between (p1, p2) and (q1, q2).
        # Good way to parse input like p1, q1? Use semicolon to separate teams?
        
    # tenzero(player)
        # return list of ten zeros
        # optionally, restrict to ten zeros for given player
        
        
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

    def parse_call(self, text, say):
        regex = re.compile('(<[^>]*>)([\w\s]*)\(([^\)]*)\)')
        try:
            groups = regex.search(text).groups()
            mention, keyword, item = [group.strip() for group in groups]
        except:
            say(token=self.SLACK_BOT_USER_TOKEN, 
                text='''Cannot parse input''')
            keyword = 'help'
            item = None
        
        return keyword, item


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
            self.Blocks.button('button_id', 'Add to Database', 'Submit', action_id='submit_game-action')
            ] 

        self.app.client.chat_postMessage(
            token=self.SLACK_BOT_USER_TOKEN,
            channel=channel,
            text = 'Add game information',
            blocks = blocks
            )
        return


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
                                                       datetime.date.today(), color[0]]
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
                    
    def handle_message_events(self, body, logger):
        logger.info(body)
        

    def handle_app_mention_events(self, event, say, ack):
        ack()
        keyword, item = self.parse_call(event['text'], say)
        
        # new game
        if keyword=='newgame':
            self.new_game(event['channel'], item)
            
        elif keyword=='newplayer':
            self.players = np.append(self.players, item)
            say(token=self.SLACK_BOT_USER_TOKEN, text=f'Added new player "{item}"')
            
        elif keyword=='help':
            say(token=self.SLACK_BOT_USER_TOKEN, 
                text='''The following are possible commands:
                    @foosbot newgame()
                    @foosbot newplayer(new_player_name)
                    @foosbot ratings()''')
                                
        elif keyword=='ratings':
            self.display_ratings(event['channel'])
        else:
            say(token=self.SLACK_BOT_USER_TOKEN, 
                text='''Did not understand command...\n
                    The following are possible commands:
                    @foosbot newgame(WO, WD, LO, LD, score, color)
                    @foosbot newplayer(new_player_name)
                    @foosbot ratings()''')

            
            
