import json
from timer import Timer
from webscraper import WebScraper as WebScr
import logging

logging.basicConfig(filename="debug.txt", level=logging.INFO)


class TransferMarkt:

    def __init__(self):
        WebScr.base_url = "https://www.transfermarkt.es"
        self.timer = Timer(0)
        self.leagues = {}
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

    def get_leagues(self, min_value=80000, force_include=None, page_num=7, additional_pages=None):
        total_teams = 0

        pages = additional_pages if isinstance(additional_pages, list) else []
        for i in range(1, page_num):
            pages.append("/wettbewerbe/europa?ajax=yw1&page=" + str(i))

        for p in pages:
            rows = self.get_rows_from_link(p)

            for row in rows:
                if 'colspan' not in row.td.attrs:
                    res = self.get_league_info(row)
                    if res and (
                            res['value'] > min_value or
                            res['id'] in force_include
                    ):
                        self.leagues[res['id']] = {}
                        self.leagues[res['id']]['name'] = res['name']
                        self.leagues[res['id']]['link'] = res['link']
                        self.leagues[res['id']]['teams'] = self.get_teams(res['link'])
                        total_teams += res['n_teams']

        self.timer = Timer(total_teams)

    @staticmethod
    def get_league_info(row):
        a_elements = row.find_all('a')
        a = a_elements[1]
        td_elements = row.find_all('td', recursive=False)

        # Name
        name = a.text.strip()
        # Link
        link = a['href']
        # Id
        aux = link.split('/')
        id_league = aux[4]
        # Country
        country = td_elements[1].img['title'].strip()
        # Number of teams
        n_teams = int(td_elements[2].text.strip())
        # Value
        txt_value = td_elements[7].text.strip()
        separator = txt_value.find(',') if (',' in txt_value) else txt_value.find(' ')
        value = int(txt_value[:separator])
        if "mil millones" in txt_value:
            value *= 1000000
        elif "mill." in txt_value:
            value *= 1000

        league = {
            'id': id_league,
            'name': name,
            'link': link,
            'country': country,
            'n_teams': n_teams,
            'value': value
        }
        return league

    @staticmethod
    def get_teams(league_link):
        teams = {}
        rows = TransferMarkt.get_rows_from_link(league_link)
        for row in rows:
            aux = row.find('td', {'class': 'hauptlink no-border-links hide-for-small hide-for-pad'}).a
            name = aux.text.strip()
            link = aux['href'].replace("startseite", "kader") + "/plus/1"
            id_team = link.split('/')[4]
            teams[id_team] = {'link': link, 'name': name}
        return teams

    def iterate_teams(self, extra_team_info=True, players=True, extra_player_info=True):
        self.timer.start()
        for id_league in self.leagues:
            teams = self.leagues[id_league]['teams']
            for id_team in teams:
                team_link = teams[id_team]['link']
                page = WebScr.get_soup(team_link)

                if extra_team_info:
                    img = page.find('img', {'alt': teams[id_team]['name']})
                    if img:
                        teams[id_team]['img'] = img['src'].replace("https", "http")

                if players:
                    self.get_players(page, id_league, extra_player_info)

                self.timer.add_done()
                self.timer.print_left()

    def get_players(self, team_page, id_league, extra_info=True):
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
                aux_8 = data[8].text.strip().split('.')

                player = {
                    'league': id_league,
                    'link': aux_1a['href'],
                    'name': aux_1a['title'],
                    'position': aux_1c if aux_1c else '',
                    'dorsal': aux_0 if (len(aux_0) > 1) else '',
                    'birth': TransferMarkt.format_birth_date(aux_2) if ('/' in aux_2) else '',
                    'nationality': data[3].img['title'],
                    'height': aux_4 if (len(aux_4) > 1) else '',
                    'foot': aux_5 if (len(aux_5) > 1) else '',
                    'contract': aux_8[2] if len(aux_8) > 2 else ''
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

        # Second team
        table = page.find('table', {'class': 'auflistung'})
        rows = table.find_all('tr')
        for row in rows:
            if row.th.text.strip() == "Club actual:":
                team_1 = row.td.a['id']
                player['team'] = team_1
            if row.th.text.strip() == "2do club:":
                team_2 = row.td.a['id']
                player['team_2'] = team_2
            elif row.th.text.strip() == "3er club:":
                team_3 = row.td.a['id']
                player['team_3'] = team_3
                logging.warning("Player with 3 clubs: {}".format(player['link']))

        return player

    @staticmethod
    def format_birth_date(date):
        aux = date.split(' ')[0]
        var = aux.split('/')
        return "{}/{}/{}".format(var[2], var[1], var[0])


if __name__ == "__main__":
    force_include = [
        'A1', 'AZ1', 'BE1', 'BU1', 'C1', 'DK1', 'ES1', 'ES2', 'ES3A', 'ES3B', 'ES3C', 'ES3D', 'FR1', 'FR2',
        'GB1', 'GB2', 'GB3', 'GR1', 'ISR1', 'IT1', 'IT2', 'KAS1', 'KR1', 'L1', 'L2', 'L3', 'MO1N', 'NL1', 'NL2', 'NO1',
        'PL1', 'PO1', 'PO2', 'RO1', 'RU1', 'RU2', 'SC1', 'SE1', 'SER1', 'TR1', 'TR2', 'TS1', 'UKR1', 'UNG1', 'WER1',
        'ZYP1'
    ]
    additional_pages = ["/wettbewerbe/amerika"]

    tm = TransferMarkt()
    print("Obtaining leagues and teams...")
    tm.get_leagues(100000000, force_include, 7, additional_pages)
    print("Leagues and teams obtained!")

    print("Getting player data...")
    tm.iterate_teams()

    print("All info downloaded, saving it...")
    output = {'leagues': tm.leagues, 'players': tm.players}
    with open('output.json', 'w') as f:
        json.dump(output, f, indent=4, sort_keys=True)
    print("Done!")
