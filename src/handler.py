import boto3
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from boto3.dynamodb.conditions import Key
from operator import itemgetter

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('VisaBulletinData')
processed_urls_table = dynamodb.Table('ProcessedURLs')

def scrape_visa_bulletin(url):
    print("Processing url: ", url)

    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    employment_based_tables = soup.find_all('tbody')
    employment_based_data = []

    # Date pattern for the table cell dates
    date_pattern = r"(\d{2})([A-Z]{3})(\d{2})"

    # Extract the date from the URL
    bulletin_date_pattern = r'visa-bulletin-for-(\w+)-(\d+)\.html'
    match = re.search(bulletin_date_pattern, url)
    if match:
        month_name, year = match.groups()
        month_abbr = month_name[:3].lower()
        month_num = datetime.strptime(month_abbr, '%b').month
        bulletin_date = datetime(int(year), month_num, 1)
    else:
        bulletin_date = None

    employment_table_id = 0

    for table in employment_based_tables:
        rows = table.find_all('tr')
        countries = []
        # From 2022 till 2024 the number of rows differ
        if len(rows) < 9 or len(rows) > 12: 
            continue
        filing_type = 'Final Date' if employment_table_id == 0 else 'Filing Date'
        print("Filing Type: ", filing_type)
        employment_table_id += 1
        for row_id, row in enumerate(rows):
            cells = row.find_all('td')
            for cell_id, cell in enumerate(cells):
                clean_cell = cell.text.replace("\n", "").replace("\xa0", "").replace("  ", " ").replace("- ", "-").strip()
                if row_id == 0:
                    if cell_id != 0:
                        countries.append(clean_cell)
                else:
                    if cell_id == 0:
                        category_value = clean_cell
                    else:
                        match = re.match(date_pattern, clean_cell)
                        if match:
                            day = int(match.group(1))
                            month_str = match.group(2)
                            year = int(match.group(3)) + 2000 # Year is only last 2 digits

                            month = datetime.strptime(month_str, "%b").month
                            cell_date = datetime(year, month, day)
                        else:
                            cell_date = bulletin_date

                        try:
                            employment_based_data.append({
                                'filing_type': filing_type,
                                'country': countries[cell_id - 1],
                                'category': category_value,
                                'bulletin_date': bulletin_date.strftime("%Y-%m-%d"),
                                'date': cell_date.strftime("%Y-%m-%d")
                            })
                        except:
                            print("ERROR: Could not process the row. Row: ", row)


    return employment_based_data

# Custom serialization function for datetime objects
def datetime_serializer(obj):
    if isinstance(obj, datetime):
        return obj.strftime("%Y-%m-%d")  # Convert datetime to ISO 8601 string format
    raise TypeError(f"Type {type(obj)} not serializable")

def store_data(data):
    try:
        print("Storing data")
        for item in data:
            filing_type = item['filing_type']
            country = item['country']
            category = item['category']
            bulletin_date = datetime.strptime(item['bulletin_date'], "%Y-%m-%d")
            date = datetime.strptime(item['date'], "%Y-%m-%d")

            pk = f"FILING_TYPE#{filing_type}#CATEGORY#{category}#COUNTRY#{country}"
            sk = f"BULLETIN_DATE#{bulletin_date.strftime('%Y-%m-%d')}"

            table.put_item(
                Item={
                    'pk': pk,
                    'sk': sk,
                    'filing_type': filing_type,
                    'country': country,
                    'category': category,
                    'bulletin_date': bulletin_date.strftime("%Y-%m-%d"),
                    'date': date.strftime("%Y-%m-%d")
                }
            )
        print("Done storing data")
    except Exception as e:
        print(f"Unable to store the data, error: {e}")

def read_data(filing_type='Final Date', category='3rd', country='All Chargeability Areas Except Those Listed'):
    pk = f"FILING_TYPE#{filing_type}#CATEGORY#{category}#COUNTRY#{country}"

    response = table.query(
        KeyConditionExpression=Key('pk').eq(pk),
        ScanIndexForward=False  # Reverse the order to get the latest bulletin_date first
    )

    items = response['Items']

    # Sort the items by bulletin_date in descending order
    sorted_items = sorted(items, key=lambda x: x['sk'], reverse=True)

    # Print the header
    print(f"Retrieved the [{filing_type}] data for [{category}] for [{country}]:")

    # Print each item
    for item in sorted_items:
        date = item['date']
        bulletin_date = item['bulletin_date']
        print(f"Bulletin {bulletin_date}: {date}")

    return sorted_items

def read_data_locally(data, filing_type = 'Final Date', category = '3rd', country = 'All Chargeability Areas Except Those Listed'):
    # Filter the data based on filing_type, category, and country
    filtered_data = [entry for entry in data
                    if entry['filing_type'] == filing_type
                    and entry['category'] == category
                    and entry['country'] == country]

    # Sort the filtered data in descending order by bulletin_date
    sorted_data = sorted(filtered_data, key=itemgetter('bulletin_date'), reverse=True)

    # Print the sorted data
    for entry in sorted_data:
        print(f"Bulletin Date: {entry['bulletin_date']}, Date: {entry['date']}")

    return sorted_data

def lambda_handler(event, context):
    base_url = 'https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html'
    response = requests.get(base_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all links to visa bulletin pages
    links = soup.find_all('a', href=True)
    visa_bulletin_links = [link['href'] for link in links if '/visa-bulletin-for-' in link['href']]
    
    # Remove duplicates
    visa_bulletin_links = list(set(visa_bulletin_links))

    data = []

    # Scrape data from each visa bulletin page
    for link in visa_bulletin_links:
        if '2022' in link or '2023' in link or '2024' in link:
            # Check if the URL has been processed
            response = processed_urls_table.get_item(Key={'url': link})
            if 'Item' in response:
                print(f"Skipping URL: {link} (already processed)")
                continue

            # Process the URL
            print(f"Processing URL: {link}")
            url = f"https://travel.state.gov{link}"
            data.extend(scrape_visa_bulletin(url))

            # Store the processed URL in DynamoDB
            processed_urls_table.put_item(Item={'url': link})


    store_data(data)
    eb3_data = read_data()

    # Temporary fix so that data is at least returned.
    # eb3_data = read_data_locally(data)

    return {
        'statusCode': 200,
        'body': eb3_data
    }
