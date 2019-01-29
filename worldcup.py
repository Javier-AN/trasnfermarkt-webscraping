import json
from webscraper import WebScraper as WebScr
import logging

logging.basicConfig(filename="debug.txt", level=logging.INFO)


class TransferMarkt:

    def __init__(self):
        WebScr.base_url = "https://www.transfermarkt.es"
        self.teams = {}
        self.players = {}

    @staticmethod
    def get_rows_from_link(url):
        page = WebScr.get_soup(url)
        if page:
            return TransferMarkt.get_rows_from_page(page)

    @staticmethod
    def get_rows_from_page(page, class_name='items'):
        table = page.find('table', {'class': class_name})
        return table.tbody.find_all('tr', recursive=False)

    def get_teams(self, pages=None):
        for p in pages:
            rows = self.get_rows_from_link(p)

            for row in rows:
                tds = row.find_all('td')
                if tds:
                    team_id = tds[0].a['id']
                    team_link = tds[0].a['href'].replace("startseite", "kader") + "/plus/1"
                    team_name = tds[1].a.text
                    self.teams[team_id] = {
                        'name': team_name, 'link': team_link}

    def iterate_teams(self, extra_team_info=True, players=True, extra_player_info=True):
        teams = self.teams
        for id_team in teams:
            team_link = teams[id_team]['link']
            nation = teams[id_team]['name'].split(' ')[0]
            page = WebScr.get_soup(team_link)

            if extra_team_info:
                img = page.find('img', {'alt': teams[id_team]['name']})
                if img:
                    teams[id_team]['img'] = img['src'].replace(
                        "https", "http")

            if players:
                self.get_players(page, id_team, nation, extra_player_info)

    def get_players(self, team_page, id_team, nation, extra_info=True):
        rows = TransferMarkt.get_rows_from_page(team_page)

        for row in rows:
            data = row.find_all('td', recursive=False)
            aux_1a = data[1].find('a', {'class': 'spielprofil_tooltip'})
            id_player = aux_1a['id']

            # If the player is not yet on the list, we add him
            if id_player not in self.players:
                aux_0 = data[0].div.text.strip()
                aux_1b = data[1].table.find_all('tr')
                aux_1c = aux_1b[1].td.text.strip()
                aux_2 = data[2].text.strip()
                aux_4 = data[4].text.strip().split(' ')[0]
                aux_5 = data[5].text.strip()

                player = {
                    'link': aux_1a['href'],
                    'name': aux_1a['title'],
                    'position': aux_1c if aux_1c else '',
                    'dorsal': aux_0 if (len(aux_0) > 1) else '',
                    'birth': TransferMarkt.format_birth_date(aux_2) if ('/' in aux_2) else '',
                    'nationality': nation,
                    'height': aux_4 if (len(aux_4) > 1) else '',
                    'foot': aux_5 if (len(aux_5) > 1) else '',
                    'team': id_team
                }
                if extra_info:
                    player = TransferMarkt.get_extra_player_info(player)
                self.players[id_player] = player

    @staticmethod
    def get_extra_player_info(player):
        page = WebScr.get_soup(player['link'])

        # Secondary position
        div = page.find('div', {'class': 'nebenpositionen'})
        if div:
            txt = div.text
            position_2 = txt[txt.find(':') + 1:].strip()
            if len(position_2) > 25:
                position_2 = position_2[:25].strip()
            player['position_2'] = position_2

        return player

    @staticmethod
    def format_birth_date(date):
        aux = date.split(' ')[0]
        var = aux.split('/')
        return "{}/{}/{}".format(var[2], var[1], var[0])


if __name__ == "__main__":
    pages = ["/u-20-south-american-championship-2019/teilnehmer/pokalwettbewerb/U20F"]

    tm = TransferMarkt()
    tm.get_teams(pages)
    tm.iterate_teams()

    leagues = {
        'U20F19': {
            'name': 'Campeonato Sudamericano Sub-20 2019',
            'teams': tm.teams
        }
    }

    output = {'leagues': leagues, 'players': tm.players}
    with open('output-worldcup.json', 'w') as f:
        json.dump(output, f, indent=4, sort_keys=True)
    print("Done!")
