#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 27 15:36:11 2023

@author: nrahul11
"""

from bs4 import BeautifulSoup as Soup
import requests
import pandas as pd
import time
import random
import re

base_url = 'http://fbref.com'
big_5 = ['Premier League', 'La Liga', 'Serie A', 'Ligue 1', 'Bundesliga']
randoms = [10, 11, 12, 13, 14, 15]

def team_data_scrape(url):
    #This function takes the FBRef URL of a club team and returns a table with the Scout Report
    #of all players on that team with a Scout Report summary table available.
    
    team_table = _team_players_scrape(url)
    
    team = team_table['Team'].tolist()[0]
    
    team_list = team_table['URL'].tolist()
    
    df = pd.DataFrame(columns=['Player Name', 'Position 1', 'Position 2', 'Statistic', 'Per 90', 'Percentile Across League Grouping'])
    #Setting an empty data frame
    
    i=0
    
    while i < len(team_list):
        print("Analyzing " + team_list[i].split('/')[-1].split('-Stats')[0].replace('-', ' '))
        temp = _scout_report_scrape(team_list[i])
        df = pd.concat([df, temp], ignore_index=True)
        i = i+1
            
        time.sleep(random.choice(randoms))
   
    df['Team'] = team
    print('Done analyzing ' + team)
    return df

def drop_gk_and_convert(table):
    #This function takes a table (such as one returned by team_data_scrape), removes GKs
    #and pivots the table by statistic type
    no_gk = table.loc[table['Position 1'] != 'GK']
    new = no_gk.pivot(index = 'Player Name', columns = 'Statistic', values='Per 90')
    
    position_df = no_gk[['Player Name', 'Position 1', 'Position 2', 'Team']]
    position_df = position_df.drop_duplicates()
    
    final = new.merge(position_df, on='Player Name')
    
    return final

### league_data_scraper works but can time out on occasion.
def league_data_scraper(url):
    league_urls = _league_scrape(url)
    league = league_urls['League'].tolist()[0]
    grouping = league_urls['League Grouping'].tolist()[0]
    lg_url_lst = league_urls['URL'].tolist()
    
    df = pd.DataFrame(columns=['Player Name', 'Position 1', 'Position 2', 'Statistic', 'Per 90', 'Percentile Across League Grouping', 'Team'])

    i=0
    
    while i < len(lg_url_lst):
        print("Analyzing " + ' '.join(lg_url_lst[i].split('/')[-1].split('-')[:-1]))
        temp = _team_players_scrape(lg_url_lst[i])
        team_df = team_data_scrape(temp)
        df = pd.concat([df, team_df], ignore_index=True)
        i = i+1
        
        time.sleep(60)

    df['League'] = league
    df['League Grouping'] = grouping
    
    return df
    
### Helper Functions Built Below: ###

def _scout_report_scrape(url):
    #This function takes a fbref URL and returns the summary table
    
    name = [(url.split('/')[-1].split('-Stats')[0].replace('-', ' '))]
    #Loads the player's name into a string for the data table
    
    info = _player_info(url)
    
    load = requests.get(url)
    load_soup = Soup(load.text)
    tables = load_soup.find_all('table')
    if len(tables) == 0:
        return pd.DataFrame(columns=['Player Name', 'Position 1', 'Position 2', 'Statistic', 'Per 90', 'Percentile Across League Grouping'])
    summary_table = tables[0]
    
    if 'Scouting Report' not in summary_table.find('caption').text:
        return pd.DataFrame(columns=['Player Name', 'Position 1', 'Position 2', 'Statistic', 'Per 90', 'Percentile Across League Grouping'])
        #If the player doesn't have a Scouting Report on fbref, it returns an empty table    
    
    rows = summary_table.find_all('tr')
    #Background work to prepare the data from url for parsing
    
    df = pd.DataFrame(columns=['Player Name', 'Position 1', 'Position 2', 'Statistic', 'Per 90', 'Percentile Across League Grouping'])
    #Setting an empty data frame
    
    i=1
    temp = []
    while i < len(rows):
        row = rows[i]
        label = row.find_all('th')
        if label[0].text=='':
            temp = []
            i=i+1
            #This if clause skips the line breaks in the summary table
            
        else:
            temp.append(label[0].text)
            #Add the Statistic name to the temp list
        
            data = row.find_all('td')
            lst_data = [x.text for x in data]
            
            if '%' in lst_data[0]:
                lst_data[0] = lst_data[0].replace('%', '')
                lst_data[0] = float(lst_data[0])/100
            
            lst_data[0] = float(lst_data[0])
            lst_data[1] = lst_data[1][0:2]
            lst_data[1] = int(lst_data[1])/100
            #Add the data points for Per 90 and Percentile to the temp list. Converts strings into numerical objects
            
            temp = name + info + temp + lst_data        
            new_row_df = pd.DataFrame([temp], columns=df.columns)       
            df = pd.concat([df, new_row_df], ignore_index=True)
            #Creates a temp Data Frame with data from the row. Concats it to the existing Data Frame
        
            temp = []
            i = i+1
    
    return df

def _player_info(url):
    #This function returns the positions that the chosen players plays. If there is only one position, the second returns as NaN.
    load = requests.get(url)
    load_soup = Soup(load.text)
    info = load_soup.find_all('p')
    
    if 'Position:' in info[0].text:
        text = info[0].text
    elif 'Position:' in info[1].text:
        text = info[1].text
    else:
        text = info[2].text
    
    match = re.search(r'Position:\s*(?P<positions>[\w\xa0-]+)', text)
    
    positions = match.group('positions').split('-')
    
    if len(positions) != 2:
        positions[0] = positions[0][0:2]
        positions.append('NaN')
    
    positions = positions[0:2]
        
    return positions

def _team_players_scrape(url):
    #This function looks at a team's fbref page and returns a table of URLs for all the players on that team
    team = ' '.join(url.split('/')[-1].split('-')[:-1])
    #Get the team name for the table
    load = requests.get(url)
    load_soup = Soup(load.text)
    tables = load_soup.find_all('table')
    team_table = tables[0]
    rows = team_table.find_all('tr')
    #Background work to prepare the data from url for parsing

    df = pd.DataFrame(columns=['Player Name', 'Team', 'URL'])
    #Setting an empty data frame
    
    i = 2
    temp = []    
    
    while i < len(rows):
        if rows[i].find('a') is None:
            break 
            #Break the loop when it reaches the end of the player names        
        
        tgt_url = rows[i].find('a').get('href')
        tgt_url = base_url + tgt_url
        name = tgt_url.split('/')[-1].split('-Stats')[0].replace('-', ' ')
        temp = [name, team, tgt_url]

        new_row_df = pd.DataFrame([temp], columns=df.columns)
     
        df = pd.concat([df, new_row_df], ignore_index=True)
     
        temp = []
        i = i+1
         
    return df    

    
def _league_scrape(url):
    #This function looks at a league's fbref page and returns a table of FBref URLs for all the teams in that league.
    
    comp = url.split('/')[-1].split('-Stats')[0].replace('-', ' ')
    #Get the League Name for the table
    
    load = requests.get(url)
    load_soup = Soup(load.text)
    tables = load_soup.find_all('table')
    team_table = tables[0]
    rows = team_table.find_all('tr')
    #Background work to prepare the data from url for parsing
    
    df = pd.DataFrame(columns=['League', 'Team', 'URL'])
    #Blank table
    
    i=1
    temp = []
    
    while i < len(rows):
        tgt_url = rows[i].find('a').get('href')
        tgt_url = base_url + tgt_url
        team = ' '.join(tgt_url.split('/')[-1].split('-')[:-1])
        temp = [comp, team, tgt_url]
        
        new_row_df = pd.DataFrame([temp], columns=df.columns)
    
        df = pd.concat([df, new_row_df], ignore_index=True)
    
        temp = []
        i = i+1
    
    if comp in big_5:
        df['League Grouping'] = 'Big 5'
    else:
        df['League Grouping'] = 'Non Big 5'
        
    return df    
    