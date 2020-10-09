import argparse
import pandas as pd
from discogs_client.exceptions import HTTPError
from datetime import datetime, timedelta
from time import sleep, time
from bs4 import BeautifulSoup
from csv import writer
from lib.convert import create_db, prepare_df
from pathlib import Path
import discogs_client
import requests
import re


# Put your developer token below. Get it at: https://www.discogs.com/settings/developers
developer_token = 'your-token-here'

# Initialize client
discogs_cl = discogs_client.Client("PricelistDiscogs/0.9.1", user_token=developer_token)

# Change saved values below. Pass the base url and label for data maintenance.
quick_url = 'https://www.discogs.com/sell/list?sort=listed%2Cdesc&limit=250&ships_from=Poland&format=Vinyl&style=House&page=1'
# It will be used in filename convention.
quick_label = 'Breaks_PL'


# Set 'wants'. Engine will look only for records with more wants than given below.
wants = 100

# Uncommented condition will NOT be scraped for release and sales statistics
conditions = (
    # 'Mint (M)'
    # 'Near Mint (NM or M-)'
    # 'Very Good Plus (VG+)'
    'Very Good (VG)',
    'Good Plus (G+)',
    'Good (G)',
    'Fair (F)', 'Poor (P)'
)

# Setting up temporary csv file
csv_headers = 'id,title,price,ratio,start,avg_rating,rating_count,low,med,high,want,have,seller,ships_from,label,' \
              'last_sold,for_sale,url,styles,comment,condition,shipping_cost\n'

temp_path = Path('lib/temp.csv')
if not temp_path.exists():
    temp_path.touch()
    temp_path.write_text(csv_headers)

temp_df = pd.read_csv(temp_path, encoding='utf-8')


# The first object is lightweight and fast to compute as it is scraped from single response page
# It keeps variables used for first filtration like item listing id (id), condition, "haves and wants",
class SearchListObject:
    def __init__( self, listing_select_soup ):
        self.soup = BeautifulSoup(str(listing_select_soup), 'html.parser')

        self.id = self.get_item_id()
        self.have = self.get_have()
        self.want = self.get_want()
        self.condition = self.get_condition()
        self.comment = self.get_comment()

        self.seller = self.soup.select('a[href$=profile]')[0].text
        self.release_link = 'www.discogs.com' + self.soup.find('a', 'item_release_link hide_mobile')['href']
        self.link = 'www.discogs.com' + self.soup.find('a', 'item_description_title')['href']
        self.title = self.soup.find('a', 'item_description_title').text

    def get_comment( self ):
        load = self.soup.select('p.hide_mobile')[1].get_text()
        comment = re.sub(r'\s*\n\s*', '', str(load).lower())
        return comment if comment else '0'

    def get_condition( self ):
        try:
            return self.soup.select('i[data-condition]')[0].get('data-condition')
        except IndexError:
            condition = re.findall('(?<=Media:)\s*(.*)(?!Sleeve)', self.soup.select('p.item_condition')[0].get_text())
            return condition[0]

    def get_have( self ):
        try:
            indicator = self.soup.find_all('span', 'have_indicator')
            have_soup = BeautifulSoup(str(indicator[0]), 'html.parser')
            have = int(have_soup.find('span', 'community_number').text)
            return have
        except IndexError:
            return 0

    def get_want( self ):
        try:
            indicator = self.soup.find_all('span', 'want_indicator')
            want_soup = BeautifulSoup(str(indicator[0]), 'html.parser')
            want = int(want_soup.find('span', 'community_number').text)
            return want
        except IndexError:
            return 0

    def get_item_id( self ):
        item_select = self.soup.select('a[data-item-id]')
        try:
            for i in range(len(item_select)):
                if item_select[i].get('data-item-id') == '':
                    pass
                else:
                    return int(item_select[i].get('data-item-id'))
        except IndexError:
            return 0


# Creation of second object is more time-consuming as it needs to make additional requests with release page
# and Discogs Client. Object takes data load generated from SearchListObject and label as additional label.
# Then it generates new features like sales statistics, ratings and ratios.
class DataFrameObject:
    def __init__( self, id, rls_link, seller, have, want, item_title, condition, comment, query ):
        self.id, self.release_link, self.seller, self.title = id, rls_link, seller, item_title
        self.have, self.want, self.condition, self.comment = have, want, condition, comment

        self.lst_url = 'https://www.discogs.com/sell/item/' + str(self.id)
        self.lst_response = requests.get(self.lst_url)
        self.lst_soup = BeautifulSoup(self.lst_response.content, 'html.parser')
        self.release_soup = self.release_request()

        self.price = self.item_price(id)
        self.start = self.get_start_price()
        self.low = self.get_release_stats('Lowest')
        self.med = self.get_release_stats('Median')
        self.high = self.get_release_stats('Highest')

        self.for_sale = re.findall('strong>(\d*)(?:.*For Sale)', str(self.release_soup.select('a')))[0]
        self.avg_rating = self.get_avg_rating()
        self.rating_count = self.get_rating_count()
        self.last_sold = self.get_last_sold()
        self.styles = self.get_styles()
        self.ships_from = self.get_ships_from()
        self.shipping_cost = self.get_shipping_cost()
        self.ratio = self.get_ratio()
        self.query = query

    def release_request( self ):
        response = requests.get('https://' + self.release_link)
        return BeautifulSoup(response.content, 'html.parser')

    def get_release_stats( self, key_string ):
        indicator = self.release_soup.select('ul')
        pattern = '(?:' + key_string + ':</h4>\s*€)(\d*.\d\d)'
        price = re.findall(pattern, str(indicator), re.DOTALL)
        try:
            price = float(price[0])
            return price
        except ValueError:
            price = float(re.sub(",", "", str(price[0])))
            price *= 10
            return price
        except IndexError:
            return 0

    def get_last_sold( self ):
        try:
            return re.findall('(?:story/\d*">\d\d\s)(.*\s\d\d)<', str(self.release_soup.select('ul')))[0]
        except IndexError:
            return 'never sold'

    def get_avg_rating( self ):
        try:
            return re.findall('(?:rating_value">)(\d.\d*)', str(self.release_soup.select('ul')))[0]
        except IndexError:
            return 0

    def get_rating_count( self ):
        try:
            return re.findall('(?:rating_count">)(\d*)', str(self.release_soup.select('ul')))[0]
        except IndexError:
            return 0

    def get_start_price( self ):
        try:
            load = re.findall('(?:price">\W)(\d*.\d*)', str(self.release_soup))
            return re.sub(',', '', load[0])
        except IndexError:
            return 0

    def get_ratio( self ):
        try:
            return round(float(self.price) / self.med, 2)
        except ZeroDivisionError:
            return 0

    def get_styles( self ):
        try:
            load = re.findall('(?<=>Style:</div>.<div class="content">\n\s)(.*?)(?=\n\s*</d)', str(self.lst_soup),
                              re.DOTALL)
            load = re.sub(' ', '', load[0])
            load = re.sub('\n', '', load).split(',')
            return load
        except IndexError:
            print('Sorry {}{} made an Index error at get_styles :('.format(self.release_link, self.id))
            return 0

    def get_ships_from( self ):
        try:
            load = re.findall('(?<=>Item Ships From:</strong>\s)(\w+\s*\w+\s*)', str(self.lst_soup), re.DOTALL)
            return load[0]
        except IndexError:
            print('Sorry ships_from made an error for {} :('.format(self.id))
            return 0

    def get_shipping_cost( self):
        try:
            load = re.findall('(?<="reduced">)(?:.*)(?:[$£¥€])(\d+.\d+)\s(?:shipping)', str(self.lst_soup), re.DOTALL)
            return float(load[0])
        except ValueError:
            load = float(re.sub(",", "", str(load[0])))
            load *= 0.0080
            return load
        except IndexError:
            return 0

    def csv_object( self ):
        url = self.lst_url
        styles = str(self.styles).replace("', '", ';')
        comment = str(self.comment).replace(',', '.').encode('utf-8')
        title = self.title.encode('utf-8')
        columns = (self.id, title, self.price, self.ratio, self.start, self.avg_rating, self.rating_count,
                   self.low, self.med, self.high, self.want, self.have, self.seller, self.ships_from, self.query,
                   self.last_sold, self.for_sale, url, styles, comment, self.condition, self.shipping_cost)
        return columns

    def item_price( self, lst ):
        try:
            if lst != 0:
                return round(discogs_cl.listing(lst).price.value, 2)
            else:
                return 0
        except HTTPError as err:
            print("HTTP Error " + str(err.status_code), end=" ")
            if err.status_code == 404:
                print("Item not found ")
                return 0
            elif err.status_code == 429:
                print("Too many requests. Sleep for 100 second ")
                sleep(60)
                return self.item_price(lst)
            elif err.status_code == 403:
                print("Forbidden, probably just deleted")
                return 0
            else:
                print(str(err.status_code) + " HTTP error ")
                pass


class Process:
    def __init__( self, url_site, query ):
        self.url_site = url_site
        self.query = query
        self.total = 0
        self.pagination()

    def catch_page( self ):
        if '&page=' in self.url_site:
            page_number = re.findall('(?<=&page=)\d*', self.url_site)
            return page_number[0]
        else:
            return 1

    def pagination( self ):
        page = int(self.catch_page())
        url = re.sub('&page=\d*', '', self.url_site)
        while True:
            try:
                url_page = url.strip(' ') + '&page=' + str(page)
                print(url_page, end=' ')

                self.scrape_page(url_page)

                page += 1
            except KeyError:
                print('Checked ' + str(page - 1) + ' pages.')
                break

    # Main engine for scraping data, reads first-hand information and makes first filtration
    def scrape_page( self, url_page ):
        search_url = requests.get(url_page)
        soup = BeautifulSoup(search_url.content, 'html.parser')
        list_of_listings_soup = soup.select("tr.shortcut_navigable")
        self.iterate_search_results(list_of_listings_soup, temp_df)

    def iterate_search_results( self, soup_select, df_temp ):
        page_total = len(soup_select)
        print(str(page_total), 'listings found')
        if page_total == 0:
            raise KeyError
        else:
            self.total += page_total
        i = count = 0
        while i < len(soup_select):
            listing_select = soup_select[i]
            item = SearchListObject(listing_select)
            print(item.id)
            load = [item.id, item.release_link, item.seller, item.have, item.want, item.title, item.condition,
                    item.comment]
            if item.condition in conditions or item.want < wants or item.id in df_temp['id'].values \
                    or 'only' in item.comment.strip():
                # or 'missing' in item.comment.strip() or item.have > item.want:
                count += 1
                i += 1
            else:
                offer = DataFrameObject(*load, self.query)
                count += 1
                i += 1

                # Second engine creates advanced object with additional scraping at each release page
                # It is updating database with each line

                print(offer.title, offer.lst_url)
                row = offer.csv_object()
                with temp_path.open('a', newline='', encoding='utf-8') as temp:
                    csv_writer = writer(temp)
                    csv_writer.writerow(row)
                i += 1

        print('\n --> ' + str(count) + ' rejected ' + str(page_total - count) + ' new potentials ')


def write_and_clean(loc):
    df = prepare_df(temp_path)
    create_db(df, loc)
    if Path(loc).exists():
        temp_path.unlink()


def main():
    try:
        t = time()
        timestamp = datetime.fromtimestamp(t).strftime('_%Y%m%d_%H_%M_%S')

        url, label = args_parser()
        process = Process(url, label)

        loc = 'out/{}_{}_total{}.csv'.format(label, process.total, timestamp)
        write_and_clean(loc)

        df = pd.read_csv(loc)
        view = ['price', 'discount', 'seller', 'ratio', 'for_sale', 'want', 'url', 'ships_from', 'shipping_cost']
        print(df[view].sort_values(by='discount', ascending=False).head(10))

        elapsed = time() - t
        time_format = timedelta(seconds=elapsed)
        print('>>> Executed in {} s'.format(time_format))

    except TypeError:
        print('\n')
        pass
    except KeyboardInterrupt:
        print(' [+] Keyboard Interrupt. Closing program.')
        exit()


def args_parser():
    description = "Scrape engine creating cvs files for further machine learning analysis and"
    url_h = "Paste your url"
    label_h = "Name it"

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-u', '--url', dest="url", type=str, help=url_h)
    parser.add_argument('-l', '--label', dest="label", type=str, help=label_h)

    args = parser.parse_args()
    url = str(args.url)
    label = args.label

    if args.url is None:
        url = quick_url

    if args.label is None:
        label = quick_label

    return url, label


main()
