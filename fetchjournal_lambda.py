import json
import urllib.request
from datetime import datetime

def lambda_handler(event, context):
    # Check if 'journal_issn' is passed in the event and is not empty
    journal_issn = event.get('journal_issn')
    
    if not journal_issn or journal_issn.strip() == "":
        return {
            'statusCode': 400,
            'body': json.dumps('Error: journal_issn parameter is required.')
        }

    base_url = f"https://api.crossref.org/journals/{journal_issn}/works"

    # Get the current year and calculate the starting year (3 years back)
    current_year = datetime.now().year
    start_year = current_year - 3

    # Query parameters
    params = f"?filter=from-pub-date:{start_year},until-pub-date:{current_year}&rows=500&sort=published&order=desc"

    # Complete URL
    request_url = base_url + params

    try:
        # Send the request to CrossRef API
        with urllib.request.urlopen(request_url) as response:
            # Check the status code
            if response.status == 200:
                data = json.loads(response.read().decode())

                # Create a list to store the data
                articles = []

                # Loop through the items and add to the list
                for item in data.get("message", {}).get("items", []):
                    title = item["title"][0] if item.get("title") else "na"
                    pub_date = item.get("created", {}).get("date-parts", [[None]])[0]  # Get only the date part (without time)
                    if pub_date and len(pub_date) == 3:
                        pub_date_str = f"{pub_date[0]}-{pub_date[1]:02d}-{pub_date[2]:02d}"  # Format as YYYY-MM-DD
                    else:
                        pub_date_str = "na"

                    volume = item.get("volume", "na")
                    issue = item.get("issue", "na")
                    article_number = item.get("article-number", "na")
                    doi = f"https://doi.org/{item['DOI']}" if item.get("DOI") else "na"

                    articles.append({
                        "Title": title,
                        "PublicationDate": pub_date_str,
                        "Volume": volume,
                        "Issue": issue,
                        "ArticleNumber": article_number,
                        "DOI": doi
                    })

                # Sort the articles by Volume, Issue, and Article Number in descending order
                articles = sorted(articles, key=lambda x: (x['Volume'], x['Issue'], x['ArticleNumber'], x['PublicationDate']), reverse=True)

                # Return the sorted articles as JSON
                return {
                    'statusCode': 200,
                    'body': json.dumps(articles)
                }
            else:
                return {
                    'statusCode': response.status,
                    'body': json.dumps({'error': 'Failed to retrieve data from CrossRef API.'})
                }

    except urllib.error.URLError as e:
        # Return an error message in case of a URL error
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
