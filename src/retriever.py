import boto3
import json
from boto3.dynamodb.conditions import Key
from enums import FilingType, Country, Category

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('VisaBulletinData')

def read_data(filing_type, category, country):
    pk = f"FILING_TYPE#{filing_type.value}#CATEGORY#{category.value}#COUNTRY#{country.value}"

    response = table.query(
        KeyConditionExpression=Key('pk').eq(pk),
        ScanIndexForward=False  # Reverse the order to get the latest bulletin_date first
    )

    items = response['Items']

    # Sort the items by bulletin_date in descending order
    sorted_items = sorted(items, key=lambda x: x['sk'], reverse=True)

    date_list = []    

    for item in sorted_items:
        date = item['date']
        bulletin_date = item['bulletin_date']
        date_list.append({"bulletin_date":bulletin_date, "date": date})

    return date_list

def lambda_handler(event, context):

    query_params = event.get('queryStringParameters', {})
    filing_type_str = query_params.get('filing_type', FilingType.FINAL_DATE.name)
    country_str = query_params.get('country', Country.ALL_AREAS)
    category_str = query_params.get('category', Category.THIRD.name)

    # Convert string values to enum members
    filing_type = FilingType[filing_type_str.upper()]
    country = Country[country_str.upper()]
    category = Category[category_str.upper()]
    
    data = read_data(filing_type, category, country)

    response = {
        "filing_type": filing_type.value,
        "category": category.value,
        "country": country.value,
        "data": data
    }

    return {
        "statusCode": 200,
        "body": json.dumps(response)
    }
