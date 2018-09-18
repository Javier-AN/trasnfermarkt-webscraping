import json
from timer import Timer
from webscraper import WebScraper as WebScr


class TransferMarkt:

    def __init__(self):
        WebScr.base_url = "https://www.transfermarkt.es"
        self.timer = Timer(0)

    @staticmethod
    def get_rows_from_link(url):
        page = WebScr.get_soup(url)
        if page:
            return TransferMarkt.get_rows_from_page(page)

    @staticmethod
    def get_rows_from_page(page):
        table = page.find('table', {'class': 'items'})
        return table.tbody.find_all('tr', recursive=False)

    def get_leagues(self, min_value=80000, force_include=None):
        leagues = {}
        total_teams = 0
        first_tier = True
        for i in range(1, 7):
            if first_tier:
                rows = self.get_rows_from_link("/wettbewerbe/europa?ajax=yw1&page=" + str(i))

                for row in rows:
                    if 'colspan' not in row.td.attrs:
                        res = self.get_league_info(row)
                        if res and (
                                res['value'] > min_value or
                                res['id'] in force_include
                        ):
                            leagues[res['id']] = {}
                            leagues[res['id']]['name'] = res['name']
                            leagues[res['id']]['link'] = res['link']
                            total_teams += res['n_teams']

        self.timer = Timer(total_teams)
        return leagues

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

    def get_teams(self, leagues, extra_player_positions=False):
        for id_league in leagues:
            teams = {}
            rows = self.get_rows_from_link(leagues[id_league]['link'])

            for row in rows:
                link = row.find('a')['href'].replace("startseite", "kader") + "/plus/1"
                id_team = link.split('/')[4]
                page = WebScr.get_soup(link)
                if page:
                    name = page.find('h1', {'itemprop': 'name'}).span.text
                    players = TransferMarkt.get_players(TransferMarkt.get_rows_from_page(page))
                    if extra_player_positions:
                        for id_player in players:
                            players[id_player] = TransferMarkt.get_extra_player_position(players[id_player])
                    teams[id_team] = {'link': link, 'name': name, 'players': players}
                    self.timer.add_done()
                    self.timer.print_left()
            leagues[id_league]['teams'] = teams
        return leagues

    @staticmethod
    def get_players(rows):
        players = {}

        for row in rows:
            data = row.find_all('td', recursive=False)
            aux_0 = data[0].div.text.strip()
            aux_1a = data[1].find('a', {'class': 'spielprofil_tooltip'})
            aux_1b = data[1].table.find_all('tr')
            aux_1c = aux_1b[1].td.text.strip()
            aux_2 = data[2].text.strip()
            aux_4 = data[4].text.strip().split(' ')[0]
            aux_5 = data[5].text.strip()
            aux_8 = data[8].text.strip().split('.')
            id_player = aux_1a['id']

            player = {
                'position': aux_1c if aux_1c else '',
                'dorsal': aux_0 if (len(aux_0) > 1) else '',
                'link': aux_1a['href'],
                'name': aux_1a['title'],
                'birth': TransferMarkt.format_birth_date(aux_2) if ('/' in aux_2) else '',
                'nationality': data[3].img['title'],
                'height': aux_4 if (len(aux_4) > 1) else '',
                'foot': aux_5 if (len(aux_5) > 1) else '',
                'contract': aux_8[2] if len(aux_8) > 2 else ''
            }
            players[id_player] = player
        return players

    @staticmethod
    def get_extra_player_position(player):
        page = WebScr.get_soup(player['link'])
        div = page.find('div', {'class': 'nebenpositionen'})
        if div:
            txt = div.text
            position_2 = txt[txt.find(':') + 1:].strip()
            if len(position_2) > 25:
                position_2 = position_2[:25].strip()
            player['position_2'] = position_2
        print(player)
        return player

    @staticmethod
    def format_birth_date(date):
        aux = date.split(' ')[0]
        var = aux.split('/')
        return "{}/{}/{}".format(var[2], var[1], var[0])


if __name__ == "__main__":
    force_include = [
        'GB1', 'L1', 'IT1', 'FR1', 'RU1', 'NL1', 'PO1', 'AZ1', 'KR1', 'RO1', 'SE1', 'SER1', 'WER1'
        'GB2', 'L2', 'IT2', 'FR2', 'RU2', 'NL2', 'PO2',
        'GB3', 'L3',
        'ES1', 'ES2', 'ES3A', 'ES3B', 'ES3C', 'ES3D',
    ]

    tm = TransferMarkt()
    print("Obtaining leagues...")
    leagues = tm.get_leagues(80000, force_include)
    print("Leagues obtained!")

    print("Getting team and player data from each league...")
    teams = tm.get_teams(leagues, extra_player_positions=False)
    print("All info downloaded, saving it...")
    with open('output.json', 'w') as f:
        json.dump(leagues, f, indent=4, sort_keys=True)
    print("Done!")
