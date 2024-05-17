import argparse
from datetime import datetime
import json
import os
import re
import time
import pandas as pd
from urllib.request import urlopen
from urllib.error import HTTPError
import bs4
import pandas as pd
import asyncio

import os
import argparse
import json
from datetime import datetime
import aiohttp
import asyncio


#Doesn't Work 
# def get_all_lists(soup):

#     lists = []
#     list_count_dict = {}

#     if soup.find('a', text='More lists with this book...'):

#         lists_url = soup.find('a', text='More lists with this book...')['href']

#         source = urlopen('https://www.goodreads.com' + lists_url)
#         soup = bs4.BeautifulSoup(source, 'lxml')
#         lists += [' '.join(node.text.strip().split()) for node in soup.find_all('div', {'class': 'cell'})]

#         i = 0
#         while soup.find('a', {'class': 'next_page'}) and i <= 10:

#             time.sleep(2)
#             next_url = 'https://www.goodreads.com' + soup.find('a', {'class': 'next_page'})['href']
#             source = urlopen(next_url)
#             soup = bs4.BeautifulSoup(source, 'lxml')

#             lists += [node.text for node in soup.find_all('div', {'class': 'cell'})]
#             i += 1

#         # Format lists text.
#         for _list in lists:
#             # _list_name = ' '.join(_list.split()[:-8])
#             # _list_rank = int(_list.split()[-8][:-2]) 
#             # _num_books_on_list = int(_list.split()[-5].replace(',', ''))
#             # list_count_dict[_list_name] = _list_rank / float(_num_books_on_list)     # TODO: switch this back to raw counts
#             _list_name = _list.split()[:-2][0]
#             _list_count = int(_list.split()[-2].replace(',', ''))
#             list_count_dict[_list_name] = _list_count

#     return list_count_dict

#Doesn't work
# def get_shelves(soup):

#     shelf_count_dict = {}
    
#     if soup.find('a', text='See top shelves…'):

#         # Find shelves text.
#         shelves_url = soup.find('a', text='See top shelves…')['href']
#         source = urlopen('https://www.goodreads.com' + shelves_url)
#         soup = bs4.BeautifulSoup(source, 'lxml')
#         shelves = [' '.join(node.text.strip().split()) for node in soup.find_all('div', {'class': 'shelfStat'})]
        
#         # Format shelves text.
#         shelf_count_dict = {}
#         for _shelf in shelves:
#             _shelf_name = _shelf.split()[:-2][0]
#             _shelf_count = int(_shelf.split()[-2].replace(',', ''))
#             shelf_count_dict[_shelf_name] = _shelf_count

#     return shelf_count_dict


def get_genres(soup):
    genres_div = soup.find("div", {"data-testid": "genresList"})
    
    if genres_div:
        
        genre_links = genres_div.find_all("a", class_="Button--tag-inline")
        
        genres = [link.text.strip() for link in genre_links]
        
        return genres
    else:
        return []


def get_series_name(soup):
    series = soup.find(id="bookSeries").find("a")
    if series:
        series_name = re.search(r'\((.*?)\)', series.text).group(1)
        return series_name
    else:
        return ""


def get_series_uri(soup):
    series = soup.find(id="bookSeries").find("a")
    if series:
        series_uri = series.get("href")
        return series_uri
    else:
        return ""


# def get_top_5_other_editions(soup):
#     other_editions = []
#     for div in soup.findAll('div', {'class': 'otherEdition'}):
#       other_editions.append(div.find('a')['href'])
#     return other_editions


def get_publication_info(soup):
    publication_info_list = []
    a = soup.find_all('div', class_='FeaturedDetails')
    for item in a:
        publication_info = item.find('p', {'data-testid': 'publicationInfo'}).text
        publication_info_list.append(publication_info)
    return publication_info_list

def get_num_pages(soup):
    number_of_pages_list = []
    featured_details = soup.find_all('div', class_='FeaturedDetails')
    for item in featured_details:
        format_info = item.find('p', {'data-testid': 'pagesFormat'})
        if format_info:
            format_text = format_info.text
            parts = format_text.split(', ')
            if len(parts) == 2:
                number_of_pages, _ = parts
                # Extract the number from the string
                number_of_pages = ''.join(filter(str.isdigit, number_of_pages))
                number_of_pages_list.append(number_of_pages)
            elif len(parts) == 1:
                # Check if it's a number
                if parts[0].isdigit():
                    number_of_pages_list.append(parts[0])
                else:
                    number_of_pages_list.append(None)  
            else:
                number_of_pages_list.append(None) 
        else:
            number_of_pages_list.append(None)  
    return number_of_pages_list

def get_format_info(soup):
    format_info_list = []
    a = soup.find_all('div', class_='FeaturedDetails')
    for item in a:
        format_info = item.find('p', {'data-testid': 'pagesFormat'}).text
        format_info_list.append(format_info)
    return format_info_list


def get_rating_distribution(soup):
    rating_numbers = {}

    try:
        rating_bars = soup.find_all('div', class_='RatingsHistogram__bar')

        # Iterate through each rating bar
        for rating_bar in rating_bars:
            try:
                # Extract the rating (number of stars) from the aria-label attribute
                rating = rating_bar['aria-label'].split()[0]

                # Extract the number of ratings from the aria-label attribute of the labelTotal div
                label_total = rating_bar.find('div', class_='RatingsHistogram__labelTotal')
                num_ratings = label_total.get_text().split(' ')[0]

                # Store the rating number in the dictionary
                rating_numbers[rating] = num_ratings
            except (KeyError, IndexError) as e:
                print(f"Error occurred while extracting rating number for {rating}: {e}")
                # Set rating number to 0 if not found
                rating_numbers[rating] = '0'
    except AttributeError as e:
        print(f"Error occurred while finding rating bars: {e}")

    return rating_numbers


def get_cover_image_uri(soup):
    series = soup.find('img', class_='ResponsiveImage')
    if series:
        series_uri = series.get('src')
        return series_uri
    else:
        return ""
    
def book_details(soup):

    try:
        return soup.find('div',class_='DetailsLayoutRightParagraph').text
    except:
        return ' '



def contributor_info(soup):
    contributor = soup.find('a', {'class': 'ContributorLink'})
    return contributor  




# def scrape_book(book_id,soup):
#     print(f'book id {book_id} done')

#     return { 'book_id':              book_id,#done
#             'cover_image_uri':      get_cover_image_uri(soup),#done
#             'book_title':           ' '.join(soup.find('h1', {'data-testid': 'bookTitle'}).text.split()),#done
#             'book_details':         book_details(soup), #Added
#             'format':               get_format_info(soup),#Added
#             'publication_info':     get_publication_info(soup),#Added
#             'authorlink':           contributor_info(soup)['href'],#done
#             'author':               contributor_info(soup).find('span', {'class': 'ContributorLink__name'}).text.strip(),#done
#             'num_pages':            get_num_pages(soup),#Added/done
#             'genres':               get_genres(soup),#done
#             'num_ratings':          ''.join(filter(str.isdigit, soup.find('span', {'data-testid': 'ratingsCount'}).text)),#done
#             'num_reviews':          ''.join(filter(str.isdigit, soup.find('span', {'data-testid': 'reviewsCount'}).text)),#done
#             'average_rating':       soup.find('div', {'class': 'RatingStatistics__rating'}).text.strip(),#done
#             'rating_distribution':  get_rating_distribution(soup)}#done

def condense_books(books_directory_path):

    books = []
    
    # Look for all the files in the directory and if they contain "book-metadata," then load them all and condense them into a single file
    for file_name in os.listdir(books_directory_path):
        if file_name.endswith('.json') and not file_name.startswith('.') and file_name != "all_books.json" and "book-metadata" in file_name:
            _book = json.load(open(books_directory_path + '/' + file_name, 'r')) #, encoding='utf-8', errors='ignore'))
            books.append(_book)

    return books

# Asynchronous function to fetch HTML content of a URL
async def _fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

# Asynchronous function to fetch HTML content for all URLs
async def _fetch_all(session, urls):
    tasks = [_fetch(session, url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# Asynchronous function to get HTML content of all URLs
async def _html_content(urls):
    connector = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=connector) as session:
        results = await _fetch_all(session, urls)
        return results

# Function to get contributor info from the soup
def contributor_info(soup):
    contributor = soup.find('a', {'class': 'ContributorLink'})
    return contributor



def book_title(soup,book_id):
    return ' '.join(soup.find('h1', {'data-testid': 'bookTitle'}).text.split())

# Function to scrape book details
def scrape_book(book_id, soup):
    print(f'book id {book_id} done')
    return {
        'book_id': book_id,
        'cover_image_uri': get_cover_image_uri(soup),
        'book_title': book_title(soup=soup,book_id=book_id),
        'book_details': book_details(soup),
        'format': get_format_info(soup),
        'publication_info': get_publication_info(soup),
        'authorlink': contributor_info(soup)['href'],
        'author': contributor_info(soup).find('span', {'class': 'ContributorLink__name'}).text.strip(),
        'num_pages': get_num_pages(soup),
        'genres': get_genres(soup),
        'num_ratings': ''.join(filter(str.isdigit, soup.find('span', {'data-testid': 'ratingsCount'}).text)),
        'num_reviews': ''.join(filter(str.isdigit, soup.find('span', {'data-testid': 'reviewsCount'}).text)),
        'average_rating': soup.find('div', {'class': 'RatingStatistics__rating'}).text.strip(),
        'rating_distribution': get_rating_distribution(soup)
    }

# Function to condense books into a single list
def condense_books(books_directory_path):
    books = []
    for file_name in os.listdir(books_directory_path):
        if file_name.endswith('.json') and not file_name.startswith('.') and file_name != "all_books.json" and "book-metadata" in file_name:
            _book = json.load(open(os.path.join(books_directory_path, file_name), 'r'))
            books.append(_book)
    return books

# # Asynchronous function to scrape a book asynchronously
# async def scrape_book_async(book_id, output_directory_path):
#     url = 'https://www.goodreads.com/book/show/' + book_id
#     html = await _html_content([url])
#     soup = bs4.BeautifulSoup(html[0], 'html.parser')
#     await asyncio.sleep(1)
#     book = scrape_book(book_id, soup)
#     output_file = os.path.join(output_directory_path, f'{book_id}_book-metadata.json')
#     with open(output_file, 'w') as f:
#         json.dump(book, f, indent=4)
#     print(f'Scraped book {book_id} to {output_file}')

# Main asynchronous function
async def main():
    start_time = datetime.now()
    script_name = os.path.basename(__file__)

    parser = argparse.ArgumentParser()
    parser.add_argument('--book_ids_path', type=str)
    parser.add_argument('--output_directory_path', type=str)
    parser.add_argument('--format', type=str, action="store", default="json",
                        dest="format", choices=["json", "csv"],
                        help="set file output format")
    args = parser.parse_args()

    book_ids = [line.strip() for line in open(args.book_ids_path, 'r') if line.strip()]
    books_already_scraped = [file_name.replace('_book-metadata.json', '') for file_name in os.listdir(args.output_directory_path) if file_name.endswith('.json') and not file_name.startswith('all_books')]
    books_to_scrape = [book_id for book_id in book_ids if book_id not in books_already_scraped]
    condensed_books_path = os.path.join(args.output_directory_path, 'all_books')

    # Fetch HTML content for all books to scrape
    urls = ['https://www.goodreads.com/book/show/' + book_id for book_id in books_to_scrape]
    html_contents = await _html_content(urls)

    # Scrape book details for each HTML content
    for book_id, html in zip(books_to_scrape, html_contents):
        if isinstance(html, Exception):
            print(f"Error fetching {book_id}: {html}")
            continue
        soup = bs4.BeautifulSoup(html, 'html.parser')
        try:
            book = scrape_book(book_id, soup)
        except:
            continue
        output_file = os.path.join(args.output_directory_path, f'{book_id}_book-metadata.json')
        with open(output_file, 'w') as f:
            json.dump(book, f, indent=4)
        print(f'Scraped book {book_id} to {output_file}')

    books = condense_books(args.output_directory_path)
    if args.format == 'json':
        with open(f"{condensed_books_path}.json", 'w') as f:
            json.dump(books, f, indent=4)
    elif args.format == 'csv':
        with open(f"{condensed_books_path}.json", 'w') as f:
            json.dump(books, f)
        book_df = pd.read_json(f"{condensed_books_path}.json")
        book_df.to_csv(f"{condensed_books_path}.csv", index=False, encoding='utf-8')

    print(str(datetime.now()) + ' ' + script_name + f':\n\n🎉 Success! All book metadata scraped. 🎉\n\nMetadata files have been output to /{args.output_directory_path}\nGoodreads scraping run time = ⏰ ' + str(datetime.now() - start_time) + ' ⏰')

if __name__ == "__main__":
    asyncio.run(main())
