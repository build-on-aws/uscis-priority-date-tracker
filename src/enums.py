from enum import Enum

class FilingType(Enum):
    FINAL_DATE = 'Final Date'
    DATES_FOR_FILING = 'Dates for Filing'

class Category(Enum):
    FIRST = '1st'
    SECOND = '2nd' 
    THIRD = '3rd'
    FOURTH = '4th'
    OTHER_WORKERS = 'Other Workers'

class Country(Enum):
    ALL_AREAS = 'All Chargeability Areas Except Those Listed'
    CHINA = 'CHINA-mainland born'
    INDIA = 'INDIA'
    MEXICO = "MEXICO"
    PHILIPPINES = 'PHILIPPINES'