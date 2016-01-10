from csv import DictReader
import random
from itertools import groupby
from collections import defaultdict
from collections import Counter
import sys


class Team:
    def __init__(self, name, seed, conf):
        self.name = name
        self.seed = seed
        self.conf = conf

    @staticmethod
    def make_team(r):
        return Team(r['Name'], r['Seed'], r['Conf'])

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return "%s (%s, %s)" % (self.name, self.seed, self.conf)

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return self.__str__().__hash__()


SUPERBOWL_TEAM = Team("SUPERBOWL", -1, "SB")


class Game:
    def __init__(self, one, two, decision_method='seed'):
        self.one = one
        self.two = two
        self.is_superbowl = (self.get_home_team() == SUPERBOWL_TEAM)
        assert (one.conf == two.conf) ^ self.is_superbowl
        if not self.is_superbowl:
            self.chance_away_team = away_vs_home_chances[one.conf][self.get_away_team().name][self.get_home_team().name]
        else:
            self.chance_away_team = .5
        self.chance_home_team = 1 - self.chance_away_team
        self.decision_method = decision_method

    def get_home_team(self):
        if self.one.conf != self.two.conf:
            return SUPERBOWL_TEAM
        if self.one.seed < self.two.seed:
            return self.one
        elif self.two.seed < self.one.seed:
            return self.two
        else:
            raise ValueError("invalid game!")

    def get_away_team(self):
        if self.one.conf != self.two.conf:
            return SUPERBOWL_TEAM
        if self.one.seed > self.two.seed:
            return self.one
        elif self.two.seed > self.one.seed:
            return self.two
        else:
            raise ValueError("invalid game!")

    def get_winner(self):
        if self.decision_method == 'seed':
            return self.get_home_team()
        elif self.decision_method == 'random':
            return self.get_random_winner()
        elif self.decision_method == 'favored':
            if self.chance_away_team > self.chance_home_team:
                return self.get_away_team()
            elif self.chance_home_team > self.chance_away_team:
                return self.get_home_team()
            else:
                raise ValueError("using favored when equal chances")

    def get_random_winner(self):
        b = random.random()
        if b <= self.chance_away_team:
            return self.get_away_team()
        else:
            return self.get_home_team()

    def get_teams(self):
        return [self.one, self.two]

    def full_str(self):
        return "%s at %s" % (self.get_away_team(), self.get_home_team())

    def __str__(self):
        return "%s at %s" % (self.get_away_team().name, self.get_home_team().name)

    def __repr__(self):
        return self.__str__()


class Round:
    def __init__(self, decision_method='seed', round_num=1):
        self.games = []
        self.decision_method = decision_method
        self.round_num = round_num

    def add_game(self, g):
        self.games.append(g)

    def add_create_game(self, one, two, decision_method=None):
        if decision_method is None:
            decision_method = self.decision_method
        g = Game(one, two, decision_method=decision_method)
        self.add_game(g)

    @staticmethod
    def create_from_winners(list_of_winners, round_num, list_of_byes=None, decision_method='seed'):
        if len(list_of_winners) == 1:
            return None
        r = Round(decision_method=decision_method, round_num=round_num)
        if list_of_byes:
            list_of_winners += list_of_byes
        list_of_winners = sorted(list_of_winners, key=lambda x: x.conf)
        teams_by_conf = groupby(list_of_winners, lambda x: x.conf)
        is_superbowl = False
        for conf, curr_teams in teams_by_conf:
            sorted_teams = sorted(curr_teams, key=lambda x: x.seed)
            # print "%s have: %s" % (conf, sorted_teams)
            if not len(sorted_teams) % 2:
                # even, not superbowl
                while len(sorted_teams):
                    high_seed = sorted_teams.pop(0)
                    low_seed = sorted_teams.pop()
                    r.add_create_game(high_seed, low_seed, decision_method=decision_method)
            else:
                is_superbowl = True
        if is_superbowl:
            assert not len(r.games)
            r.add_create_game(list_of_winners[0], list_of_winners[1], decision_method=decision_method)
        return r

    def simulate(self):
        return [g.get_winner() for g in self.games]

    def get_all_teams(self):
        teams = []
        for g in self.games:
            teams += g.get_teams()
        return teams

    def __str__(self):
        return "Round %d :: %s" % (self.round_num, str(self.games))

    def __repr__(self):
        return repr(self.games)


def init_playoffs(decision_method='seed'):
    wc = Round(decision_method=decision_method)
    wc.add_create_game(team_lookup['KC'], team_lookup['HOU'])
    wc.add_create_game(team_lookup['PIT'], team_lookup['CIN'])
    wc.add_create_game(team_lookup['SEA'], team_lookup['MIN'])
    wc.add_create_game(team_lookup['GB'], team_lookup['WAS'])
    return wc


def get_bye_teams():
    return [team_lookup['DEN'],
            team_lookup['NE'],
            team_lookup['CAR'],
            team_lookup['ARI']
            ]


def run_tournament(decision_method):
    p = init_playoffs(decision_method=decision_method)
    # print get_bye_teams()
    winners = []
    game_counts = Counter()
    weighted_game_counts = defaultdict(list)
    while p.round_num < 4:
        # print "current round:\n", p.round_num
        for t in p.get_all_teams():
            game_counts[t] += 1
            weighted_game_counts[t].append(p.round_num)
        winners = p.simulate()
        # print "produced winners:\n", winners
        if p.round_num == 1:
            p = Round.create_from_winners(winners, p.round_num+1,
                                          list_of_byes=get_bye_teams(), decision_method=p.decision_method)
        else:
            p = Round.create_from_winners(winners, p.round_num+1, decision_method=p.decision_method)
    # print game_counts
    for t in p.get_all_teams():
        game_counts[t] += 1
        weighted_game_counts[t].append(p.round_num)
    return winners, game_counts, weighted_game_counts


teams = []
team_lookup = {}

with open('teams.csv', 'rb') as infile:
    c = DictReader(infile)
    for row in c:
        t = Team.make_team(row)
        teams.append(t)
        team_lookup[t.name] = t

away_vs_home_chances = defaultdict(lambda: defaultdict(dict))
for conf in ['afc','nfc']:
    with open("%s_matchups.csv" % conf,'rb') as matchup_file:
        m = DictReader(matchup_file)
        for row in m:
            away_team_name = row['Home']
            for col_name in row.iterkeys():
                if col_name != away_team_name and col_name != 'Home' and row[col_name]:
                    away_vs_home_chances[conf.upper()][away_team_name][col_name] = float(row[col_name])

total_game_counts = Counter()
total_weighted_game_counts = defaultdict(lambda: Counter())
wins = Counter()
total = 1000000
for i in range(total):
    if i % 10000 == 0:
        sys.stdout.write('.')
        sys.stdout.flush()
    winners, game_counts, weighted_game_counts = run_tournament('random')
    for team in winners:
        wins[team] += 1
    total_game_counts += game_counts
    for team, round_nums in weighted_game_counts.items():
        for n in round_nums:
            total_weighted_game_counts[team][n] += 1
sys.stdout.write('\n')
for team in teams:
    if team not in wins:
        wins[team] = 0
    if team not in total_game_counts:
        total_game_counts[team] = 0
    if team not in total_weighted_game_counts:
        total_weighted_game_counts[team] = Counter()

print "Avg times reached superbowl"
for team, times_reached_superbowl in sorted(wins.items(), key=lambda x: x[1], reverse=True):
    print "team:%s -> %s or %.3f %%" % (team, times_reached_superbowl, float(times_reached_superbowl)/total)

print "Avg games played"
for team, count in sorted(total_game_counts.items(), key=lambda x: x[1], reverse=True):
    print "team:%s -> avg games played:%f" % (team, round(float(count) / total, 2))

print "Weights received:"
for team, cntr in sorted(total_weighted_game_counts.items(),
                         key=lambda x: (x[1][4], x[1][3], x[1][2], x[1][1]), reverse=True):
    print "team:%s -> weights received:%s" % (team, map(lambda x: "%d %s" %
            (x[0], round((float(x[1])/total), 2)),
            sorted(cntr.items(), key=lambda x: (x[0], x[1]), reverse=True)
                                                        ))