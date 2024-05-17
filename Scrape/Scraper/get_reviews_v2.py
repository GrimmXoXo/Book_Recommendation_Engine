import argparse
import asyncio
import logging
import os
import re
import sqlite3
import time
from datetime import datetime
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from langdetect import detect
import aiohttp
from database_operations import create_database,insert_review



start_time = datetime.now()
script_name = os.path.basename(__file__)

async def is_english(text):
    try:
        return detect(text) == 'en'
    except:
        return False

async def get_user_id(article):
    avatar = article.find('section', class_='ReviewerProfile__avatar')
    user_id_link = avatar.a['href']
    user_id = re.search(r'\d+', user_id_link).group()
    return user_id

async def get_rating_and_date_user(article):
    rating_date_user = article.find('section', class_='ReviewCard__row')
    date_element = rating_date_user.find('span', class_='Text__body3').find('a')
    review_date = date_element.get_text(strip=True) if date_element else None

    rating_element = rating_date_user.find('span', class_='RatingStars__small')
    aria_label = rating_element['aria-label'] if rating_element else None
    if aria_label:
        rating = aria_label 
    else:
        rating = None
    return review_date, rating

async def get_reviewers_info(review_articles, book_id):
    english_reviews_info = []

    for i, article in enumerate(review_articles):
        if i == 5:  # only first 5 reviews
            break

        # Extract review content
        review_content = article.find(class_='TruncatedContent__text').get_text(strip=True)  # working

        if await is_english(review_content):
            try:
                # Extract reviewer name
                reviewer_name = article.find(class_='ReviewerProfile__name').get_text(strip=True)
            except AttributeError:
                reviewer_name = None  

            try:
                # Extract reviewer ID
                reviewer_id = await get_user_id(article)
            except Exception as e:
                print(f"Error extracting reviewer ID: {e}")
                reviewer_id = None  

            try:
                # Extract likes on review
                likes_on_review = article.find(class_='Button--subdued').get_text(strip=True)
            except AttributeError:
                likes_on_review = None  

            try:
                # Extract reviewer followers
                reviewer_followers = article.find(class_='ReviewerProfile__meta').find_all('span')[1].get_text(strip=True)
            except (AttributeError, IndexError):
                reviewer_followers = None  

            try:
                # Extract reviewer total reviews
                reviewer_total_reviews = article.find(class_='ReviewerProfile__meta').find_all('span')[0].get_text(strip=True)
            except (AttributeError, IndexError):
                reviewer_total_reviews = None  

            try:
                # Extract review date and rating
                review_date, review_rating = await get_rating_and_date_user(article)
            except Exception as e:
                print(f"Error extracting review date and rating: {e}")
                review_date = review_rating = None  

            # Check if all fields are None
            if all(value is None for value in [reviewer_name, reviewer_id, likes_on_review, reviewer_followers, reviewer_total_reviews, review_date, review_rating]):
                continue

            english_reviews_info.append({
                'book_id': book_id,
                'reviewer_id': reviewer_id,
                'reviewer_name': reviewer_name,
                'likes_on_review': likes_on_review,
                'review_content': review_content,
                'reviewer_followers': reviewer_followers,
                'reviewer_total_reviews': reviewer_total_reviews,
                'review_date': review_date,
                'review_rating': review_rating
            })
    return english_reviews_info




async def fetch_html(session, url):
    try:
        async with session.get(url) as response:
            html_content = await response.text()
            return url, html_content, None  # No exception occurred
    except Exception as e:
        return url, None, e  # Return the exception


async def scrape_book_reviews(urls, book_ids, parsed_args):
    url_to_book_id = {f'https://www.goodreads.com/book/show/{book_id}': book_id for book_id in book_ids}

    connector = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_html(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            url, response_text, error = result  # Unpack the result
            if error is not None:
                print(f"Error fetching {url}: {error}")
                continue

            book_id = url_to_book_id[url]

            try:
                soup = BeautifulSoup(response_text, 'html.parser')
                review_articles = soup.find_all('article', class_='ReviewCard')
                results = await get_reviewers_info(review_articles, book_id)
                if results:
                    print(str(datetime.now()) + ' ' + script_name + ': Scraped ✨' + str(len(results)) + '✨ reviews for ' + book_id)
                    print('=============================')

                # Insert to db
                conn = sqlite3.connect(parsed_args.output_directory_path +'/book_reviews.db')
                for review_info in results:
                    insert_review(conn, review_info)
                conn.close()

            except HTTPError:
                print(f"HTTP Error occurred while processing {url}. Skipping book...")
                continue

            except Exception as e:
                print(f"An error occurred while processing {url}: {e}")
                logging.error("An error occurred while processing book ID %s: %s", book_id, e)




async def main():
    # Set up logging
    logging.basicConfig(filename='error.log', level=logging.ERROR)

    parsed_args = parse_arguments()

    if not parsed_args.book_ids_path:
        raise ValueError("Please provide a file path containing Goodreads book IDs using the --book_ids_path flag.")

    # Read book IDs from the file
    with open(parsed_args.book_ids_path, 'r') as f:
        book_ids = [line.strip() for line in f if line.strip()]

    # Find books that have not been scraped yet
    conn = sqlite3.connect(parsed_args.output_directory_path +'/book_reviews.db')
    c = conn.cursor()
    c.execute('SELECT book_id FROM book_reviews')
    books_already_scraped = [row[0] for row in c.fetchall()]
    books_to_scrape = [book_id for book_id in book_ids if book_id not in books_already_scraped]

    if len(books_to_scrape) == 0:
        print('All books done, No new ID to scrape')
        exit(0)

    urls = ['https://www.goodreads.com/book/show/' + book_id for book_id in books_to_scrape]

    

    await scrape_book_reviews(urls, books_to_scrape,parsed_args=parsed_args)

    if conn:
        conn.close()

    print(str(datetime.now()) + ' ' + script_name + f':\n\n🎉 Success! All book reviews scraped. 🎉\n\nGoodreads review files have been output to /{parsed_args.output_directory_path}\nGoodreads scraping run time = ⏰ ' + str(datetime.now() - start_time) + ' ⏰')


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--book_ids_path', type=str)
    parser.add_argument('--output_directory_path', type=str)
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(main())
