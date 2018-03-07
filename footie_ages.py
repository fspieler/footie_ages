#!/usr/bin/env python
# coding=utf-8
from __future__ import print_function
from __future__ import division

'''
takes football-api.com API token as command line argument
'''

import requests
from datetime import datetime
import time
import json
import sys

# RateLimited copied from https://gist.github.com/gregburek/1441055
def RateLimited(maxPerSecond):
    minInterval = 1.0 / float(maxPerSecond)
    def decorate(func):
        lastTimeCalled = [0.0]
        def rateLimitedFunction(*args,**kargs):
            elapsed = time.clock() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait>0:
                time.sleep(leftToWait)
            ret = func(*args,**kargs)
            lastTimeCalled[0] = time.clock()
            return ret
        return rateLimitedFunction
    return decorate


# documented at football-api.com
class API(object):
    def __init__(self, api_token):
        self._token = api_token
        self._base_url = 'http://api.football-api.com/2.0'
    @RateLimited(2)
    def __getitem__(self, endpoint):
        url = '{}{}?Authorization={}'.format(
            self._base_url,
            endpoint,
            self._token
        )
        print(url)
        response = requests.get(url).json()
        print(response)
        return response

a = API(sys.argv[1])
def teams():
    return sorted(
        list(map(
            lambda x: {
                'name':x['team_name'],
                'id':x['team_id'],
                'position':int(x['position'])
            },
            a['/standings/1204']
        )),
        key=lambda x: int(x['position'])
    )

def team_player_data(team_id, now=None):
    if not now: #when?
        now = datetime.now()
    team = filter(
        lambda x:int(x['minutes']) > 0,
        a['/team/{}'.format(team_id)]['squad']
    )
    ret = {}
    for player in team:
        try:
            birthdate = datetime.strptime(
                a['/player/{}'.format(player['id'])]['birthdate'],
                '%d/%m/%Y'
            )
            age = (now - birthdate).days / 365.25
        except:
            age = "ERROR"
        try:
            minutes = int(player['minutes'])
        except:
            minutes = "ERROR"
        try:
            keeper = player['position'].lower() == 'g'
        except:
            keeper = "ERROR"
        ret[player['name']] = {
            'age':age,
            'minutes':minutes,
            'is_keeper':keeper
        }

    return ret

def player_data_by_team(now=None):
    if not now: #when?
        now = datetime.now()
    ret = []
    for t in teams():
        ret.append({'name':t['name'],'position':t['position'],'player_data':team_player_data(t['id'], now)})
    return ret

def normalize(data):
    ret = []
    for team in data:
        total_minutes = 0
        outfield_minutes = 0
        keeper_minutes = 0
        for player in team['player_data'].values():
            minutes = int(player['minutes'])
            total_minutes += minutes
            if player['is_keeper']:
                keeper_minutes += minutes
            else:
                outfield_minutes += minutes
        normalized_age = 0.0
        normalized_outfield_age = 0.0
        normalized_keeper_age = 0.0
        for player in team['player_data'].values():
            age = float(player['age'])
            minutes = int(player['minutes'])
            normalized_age += age * minutes / total_minutes
            if player['is_keeper']:
                normalized_keeper_age += age * minutes / keeper_minutes
            else:
                normalized_outfield_age += age * minutes / outfield_minutes
        ret.append({
            'name':team['name'],
            'position':team['position'],
            'normalized_age':normalized_age,
            'normalized_outfield_age':normalized_outfield_age,
            'normalized_keeper_age':normalized_keeper_age
        })
    return sorted(ret, key=lambda x:x['normalized_age'])


#these lines load data from site
#with open('intermediate.json','wb') as f:
#    f.write(json.dumps(player_data_by_team(),ensure_ascii=False).encode('utf-8'))

with open('intermediate.json','rb') as f:
    teams = json.loads(f.read().decode('utf-8'))
import pprint
with open('results.json','w') as f:
    f.write(json.dumps(normalize(teams)))

