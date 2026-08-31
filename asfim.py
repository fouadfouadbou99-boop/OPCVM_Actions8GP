import pandas as pd
import requests
from bs4 import BeautifulSoup

def get_asfim_tables():

    url = "https://asfim.ma/publications/tableaux-des-performances/"

    tables = pd.read_html(url)

    return tables
