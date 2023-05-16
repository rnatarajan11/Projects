SELECT player_display_name as name, season, rush_yards, expected_rush_yards FROM RB_stats
WHERE week = 0;

SELECT player_display_name as name, season, rush_yards, expected_rush_yards FROM RB_stats
where week = 0 AND (season = 2016 or season = 2017);

DELETE FROM RB_stats
WHERE season = 2016 or season = 2017;

SELECT * FROM RB_stats where season = 2016;

SELECT TOP 10 * FROM RB_stats where season = 2018;

SELECT player_display_name AS name, season, rush_attempts, rush_yards from RB_stats
WHERE week = 0 AND season = 2022;

SELECT season, round(avg(rush_yards_over_expected_per_att),2) as avg_ryoe_per_attempt, format(avg(rush_pct_over_expected), 'P2') as avg_pct_roe from rb_stats
WHERE rush_yards > 1000 AND season_type = 'REG'
GROUP BY season;

SELECT player_short_name as name, week, 
rush_attempts, rush_yards, round(expected_rush_yards,0) as expected_rush_yards, 
round(rush_yards - expected_rush_yards,0) as yards_over_expected, 
round(rush_yards_over_expected_per_att,2) as ryoe_per_attempt, format(rush_pct_over_expected, 'P2') as avg_pct_roe from RB_stats
WHERE player_short_name = 'K.Walker' AND season_type = 'REG';

SELECT rusher_player_name as name, play_id, week, down, yrdln, yards_gained from pbp2022
WHERE rusher_player_name = 'K.Walker';

SELECT rusher_player_name as name, week, count(name) as attempts, sum(yards_gained) as rushing_yards from pbp2022
WHERE rusher_player_name = 'K.WALKER' AND week > 5 AND season_type = 'REG'
GROUP BY rusher_player_name, week;

SELECT rusher_player_name as name, week, count(name) as attempts, sum(yards_gained) as rushing_yards, sum(touchdown) as rushing_tds, 
round(sum(epa),2) as epa from pbp2022
WHERE rusher_player_name = 'K.WALKER' AND (week > 5 AND week <> 13) AND season_type = 'REG'
GROUP BY rusher_player_name, week;

CREATE TABLE walker_stats (
    week INT PRIMARY KEY,
    name varchar(10),
    attempts INT,
    rushing_yards INT,
    rushing_tds INT,
    epa FLOAT
);

INSERT INTO walker_stats (week, name, attempts, rushing_yards, rushing_tds, epa)
SELECT week, rusher_player_name as name, count(name) as attempts, sum(yards_gained) as rushing_yards, sum(touchdown) as rushing_tds, 
round(sum(epa),2) as epa from pbp2022
WHERE rusher_player_name = 'K.WALKER' AND (week > 5 AND week <> 13) AND season_type = 'REG'
GROUP BY rusher_player_name, week;

ALTER TABLE walker_stats
ADD pct_positive_epa_plays float;

UPDATE walker_stats
SET pct_positive_epa_plays = ROUND(CAST(subquery.positive_epa_count AS FLOAT) / CAST(walker_stats.attempts AS FLOAT),4)
FROM walker_stats
INNER JOIN (
    SELECT week, rusher_player_name as name, count(name) as attempts, count(case when epa > 0 then 1 end) as positive_epa_count 
    FROM pbp2022
    WHERE rusher_player_name = 'K.Walker'
    GROUP BY week, rusher_player_name
) 
AS subquery ON walker_stats.week = subquery.week AND walker_stats.name = subquery.name;

SELECT week, name, epa, format(pct_positive_epa_plays, 'P2') as pct_positive_epa_plays from walker_stats;

SELECT format(sum(attempts * pct_positive_epa_plays)/sum(attempts), 'P2') as season_positive_epa_play_pct from walker_stats;

SELECT 
    ws.name, 
    ws.week, 
    ws.attempts, 
    ws.rushing_yards, 
    ws.rushing_tds,
    round(rs.expected_rush_yards,0) as expected_rush_yards, 
    round((ws.rushing_yards - rs.expected_rush_yards),0) as ryoe,
    round(rs.rush_yards_over_expected_per_att,2) as ryoe_per_attempt,
    ws.epa, 
    round((ws.epa/ws.attempts),2) as epa_per_attempt,
    format(ws.pct_positive_epa_plays, 'P2') as pct_positive_epa_plays, 
    format(rs.rush_pct_over_expected, 'P2') as avg_pct_roe
FROM walker_stats as ws
JOIN RB_stats as rs ON ws.week = rs.week
WHERE rs.player_short_name = 'K.Walker' AND rs.season_type = 'REG';