from json import dump
from timer import Timer
from webscraper import WebScraper as WebScr


class TransferMarket:

    def __init__(self):
        WebScr.base_url = "https://www.transfermarkt.es"
        self.timer = Timer(0)

    @staticmethod
    def get_rows_from_link(url):
        page = WebScr.get_soup(url)
        if page:
            return TransferMarket.get_rows_from_page(page)

    @staticmethod
    def get_rows_from_page(page):
        table = page.find('table', {'class': 'items'})
        return table.tbody.find_all('tr', recursive=False)

    def get_leagues(self):
        leagues = {}
        total_teams = 0
        first_tier = True
        for i in range(1, 4):
            if first_tier:
                rows = self.get_rows_from_link("/wettbewerbe/europa?ajax=yw1&page=" + str(i))

                for row in rows:
                    if 'colspan' in row.td.attrs:
                        if row.td.text.strip() == "Segunda División":
                            first_tier = False
                    elif first_tier:
                        res = self.get_league_info(row)
                        if res:
                            leagues[res[0]] = {}
                            leagues[res[0]]['name'] = res[1]
                            leagues[res[0]]['link'] = res[2]
                            total_teams += res[3]
                    else:
                        res = self.get_league_info(row)
                        if res and res[1] == "LaLiga2":
                            leagues[res[0]] = {}
                            leagues[res[0]]['name'] = res[1]
                            leagues[res[0]]['link'] = res[2]
                            total_teams += res[3]
                            break

        self.timer = Timer(total_teams)
        return leagues

    @staticmethod
    def get_league_info(row):
        a_elements = row.find_all('a')
        a = a_elements[1]
        name = a.text.strip()
        link = a['href']
        aux = link.split('/')
        id_league = aux[4]
        td_elements = row.find_all('td', recursive=False)
        n_teams = int(td_elements[2].text.strip())
        return id_league, name, link, n_teams

    def get_teams(self, leagues):
        for id_league in leagues:
            teams = {}
            rows = self.get_rows_from_link(leagues[id_league]['link'])

            for row in rows:
                link = row.find('a')['href'].replace("startseite", "kader") + "/plus/1"
                id_team = link.split('/')[4]
                page = WebScr.get_soup(link)
                if page:
                    name = page.find('h1', {'itemprop': 'name'}).span.text
                    players = TransferMarket.get_players(TransferMarket.get_rows_from_page(page))
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
                'birth': TransferMarket.format_birth_date(aux_2) if ('/' in aux_2) else '',
                'nationality': data[3].img['title'],
                'height': aux_4 if (len(aux_4) > 1) else '',
                'foot': aux_5 if (len(aux_5) > 1) else '',
                'contract': aux_8[2] if len(aux_8) > 2 else ''
            }
            players[id_player] = player
        return players

    @staticmethod
    def format_birth_date(date):
        aux = date.split(' ')[0]
        var = aux.split('/')
        return "{}/{}/{}".format(var[2], var[1], var[0])


if __name__ == "__main__":
    tm = TransferMarket()
    print("Obtaining leagues...")
    leagues = tm.get_leagues()
    print("Leagues obtained!")
    print("Getting team and player data from each league...")
    teams = tm.get_teams(leagues)
    print("All info downloaded, saving it...")
    with open('output.json', 'w') as f:
        dump(leagues, f, indent=4, sort_keys=True)
    print("Done!")
