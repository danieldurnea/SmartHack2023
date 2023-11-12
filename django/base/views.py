from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response
from django.core.cache import cache
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.http import HttpResponse
import requests
import instascrape
import json
from google.cloud import language_v2
import os
import re
from google.protobuf.json_format import MessageToJson
import time
import math
from openai import OpenAI

from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from datetime import datetime


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/code/service-key.json"


CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

from .models import Base


# Create your views here.
@api_view(['GET'])
def home(request):
    # if 'base' in cache:
    #     return Response(cache.get('base'), status=status.HTTP_200_OK)
    # else:
    #     cache.set('base', [{'data': 'abc'}], timeout=CACHE_TTL)
    #     return render(request, 'static/base.html')
    r = requests.post('https://data.veridion.com/search/v1/companies', headers={
        'x-api-key': 'key',
        'Content-Type': 'application/json'
    }, json={
        "filters":[
            {
                'attribute': "company_keywords",
                'relation': 'match_expression',
                'value': {
                    'match': {
                        'operator': 'or',
                        'operands':[
                            'women owned',
                            'minority owned',
                        ]
                    }
                },
                'strictness': 3
            },
            {
                'attribute': 'company_industry',
                'relation': 'equals',
                'value': 'IT'
            }
        ]
    })

    # company_data = r.json()['result'][0]
    # company_data = {'company_name': company_data['company_name'], 'website_url': company_data['website_url'], 'company_commercial_names': company_data['company_commercial_names'], 'company_legal_names': company_data['company_legal_names']}

    # r2 = requests.post('https://data.veridion.com/match/v4/companies', headers={
    #     'x-api-key': 'Lk34BnMBMFDj07xGbkQ_aNikeD4_NSKq643WxEEuQUAcjtbrVJStX9FpASw7',
    #     'Content-Type': 'application/json'
    # }, json={
    #     'commercial_names': company_data['company_commercial_names'],
    #     'company_legal_names': company_data['company_legal_names'],
    #     'website': company_data['website_url']
    # })

    return Response(r.json(), status=status.HTTP_200_OK)

@api_view(['GET'])
def main_page(request):
    return render(request, 'static/client_company_form.html')

@api_view(['POST'])
def comparison(request):
    legal_name = request.POST.get('input1')
    website_or_phone = request.POST.get('input2')

    phone_pattern = re.compile('^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$')

    json = {}

    website = ''
    phone = ''

    if phone_pattern.match(website_or_phone):
        phone = website_or_phone
    else:
        website = website_or_phone


    if website == '':
        json = {
            'legal_names': [legal_name],
            'phone_number': phone
        }
    else:
        json = {
            'legal_names': [legal_name],
            'website': website
        }

    own_company = requests.post('https://data.veridion.com/match/v4/companies', headers={
        'x-api-key': 'key',
        'Content-Type': 'application/json'
    }, json=json)

    if own_company.status_code != 200:
        # print(own_company.json)
        return Response({'message': 'No match found'}, status=status.HTTP_404_NOT_FOUND)

    own_company = own_company.json()
    own_company['long_description'] = translate(own_company['long_description'])

    cache.set('own_company', own_company, timeout=CACHE_TTL)

    return render(request, 'static/confirm_company.html', {
        'company_legal_names': ', '.join(own_company['company_legal_names']),
        'company_commercial_names': ', '.join(own_company['company_commercial_names']),
        'primary_phone': own_company['primary_phone'],
        'emails': ', '.join(own_company['emails']),
    })

def get_other(request):
    answer = request.POST.get('answer')

    if answer == 'no':
        return render(request, 'static/client_company_form.html')

    return render(request, 'static/other_companies.html')

def compare_companies(request):
    # if 'company_data' not in cache:
    r = requests.post('https://data.veridion.com/search/v1/companies', headers={
        'x-api-key': 'key',
        'Content-Type': 'application/json'
    }, json={
        "filters": [
            {
                'attribute': "company_keywords",
                'relation': 'match_expression',
                'value': {
                    'match': {
                        'operator': 'or',
                        'operands': [request.POST.get('input3')]
                    }
                },
                'strictness': 3
            },
            {
                'attribute': "company_location",
                'relation': 'equals',
                'value': {
                    'country': request.POST.get('input4')
                }
            },
            {
                'attribute': "company_industry",
                'relation': 'equals',
                'value': request.POST.get('input2')
            }
        ]
    })

    print(r)

    company_data = r.json()['result'][:3]

    for i in range(len(company_data)):
        company_data[i]['long_description'] = translate(company_data[i]['long_description'])
        # company_data[i]['long_description'] = ''
        company_data[i]['anaf'] = anaf(company_data[i]['company_name'])
        print(company_data[i])

    # company_data['long_description'] = translate(company_data['long_description'])

    cache.set('company_data', company_data, timeout=CACHE_TTL)
    # else:
    #     company_data = cache.get('company_data')

    #comparison_result = compare_now(request)

    return compare_now(request)
    #return render(request, 'static/comparison_result.html', comparison_result)


def compare_now(request_django):
    own_company = cache.get('own_company')
    other_companies = cache.get('company_data')
    # print(other_companies[0])

    other_long_desc = []

    for dictionar in other_companies:
        other_long_desc.append(dictionar["long_description"])

    # if 'categs' not in cache:
    client = language_v2.LanguageServiceClient()
    document = language_v2.Document()
    document.content = own_company["long_description"]
    document.type= language_v2.Document.Type.PLAIN_TEXT
    request = language_v2.ModerateTextRequest(
        document=document
    )

    response = client.moderate_text(request=request)

    # Handle the response
    # categs = MessageToJson(response.moderation_categories, preserving_proto_field_name = True)
    categs = {}
    for categ in response.moderation_categories:
        cname = ''
        if categ.name == 'Death, Harm & Tragedy':
            cname = 'DHT'
        elif categ.name == 'Firearms & Weapons':
            cname = 'FW'
        elif categ.name == 'War & Conflict':
            cname = 'WC'
        elif categ.name == 'Religion & Belief':
            cname = 'RB'
        elif categ.name == 'Public Safety':
            cname = 'PS'
        elif categ.name == 'Illicit Drugs':
            cname = 'ID'
        else:
            cname = categ.name
        categs[cname] = categ.confidence

    cache.set('categs', categs, timeout=CACHE_TTL)
    # else:
    #     categs = cache.get('categs')
    #     # cache.delete('categs')

    other_categs = []
    # sum = 0
    # if 'other_categs' not in cache:
    other_categs = []
    for comp in other_companies:
        sum = 0
        client = language_v2.LanguageServiceClient()
        document = language_v2.Document()
        document.content = comp["long_description"]
        document.type = language_v2.Document.Type.PLAIN_TEXT
        request = language_v2.ModerateTextRequest(
            document=document
        )

        response = client.moderate_text(request=request)

        # Handle the response
        # categs = MessageToJson(response.moderation_categories, preserving_proto_field_name = True)
        ocategs = {}
        for categ in response.moderation_categories:
            cname = ''
            if categ.name == 'Death, Harm & Tragedy':
                cname = 'DHT'
            elif categ.name == 'Firearms & Weapons':
                cname = 'FW'
            elif categ.name == 'War & Conflict':
                cname = 'WC'
            elif categ.name == 'Religion & Belief':
                cname = 'RB'
            elif categ.name == 'Public Safety':
                cname = 'PS'
            elif categ.name == 'Illicit Drugs':
                cname = 'ID'
            else:
                cname = categ.name
            ocategs[cname] = categ.confidence

            sum += (categ.confidence - categs[cname]) ** 2

        ocategs['company_name'] = comp['company_name']
        ocategs['distance'] = sum
        ocategs['common_values'] = common_values(own_company['long_description'], comp['long_description'])
        ocategs['anaf'] = comp['anaf']
        # ocategs['common_values'] = ''
        other_categs.append(ocategs)
        time.sleep(0.5)

        cache.set('other_categs', other_categs, timeout=CACHE_TTL)
    # else:
    #     other_categs = cache.get('other_categs')
        # cache.delete('other_categs')

    return render(request_django, 'static/comparison_result.html', {"own": categs, "other_categs": other_categs})

    # r = requests.post('https://language.googleapis.com/v1/documents:moderateText', headers={
    #     'Authorization': 'Bearer ',
    #     'Content-Type': 'application/json'
    # }, json={
    #     "document": [
    #         {
    #             'type':'PLAIN_TEXT',
    #             'content': own_company["long_description"]
    #         }
    #     ]
    # })
    #
    # print(r)
    # return render(request, 'static/comparison_result.html', {"message": r.json()})

def translate(text):
    try:
        message = 'If the following text is in English, output it, otherwise translate it into English (don\'t output no other comments other than the text): ' + text

        client = OpenAI(
            # defaults to os.environ.get("OPENAI_API_KEY")
            api_key="sk-key",
        )

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": message
                }
            ],
            model="gpt-4"
        )

        # print(type(response.model_dump_json()))
        return json.loads(response.model_dump_json())['choices'][0]['message']['content']
    except:
        return text

def common_values(text1, text2):
    try:
        message = 'Find at least 2 and at most 5 key common values between the texts of these two companies\nText 1: ' + text1 + '\nText 2: ' + text2

        client = OpenAI(
            # defaults to os.environ.get("OPENAI_API_KEY")
            api_key="sk-key",
        )

        response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": message
                }
            ],
            model="gpt-4"
        )

        print(type(response.model_dump_json()))
        return json.loads(response.model_dump_json())['choices'][0]['message']['content']
    except:
        return 'NoChatGPT'

def scrape(nume):
    try:
        # Specify the path to your webdriver executable. You may need to download the appropriate driver for your browser.
        # Create a new instance of the Chrome driver (you can use other drivers like Firefox, Edge, etc.)
        service = ChromeService(executable_path=ChromeDriverManager().install())

        options = webdriver.ChromeOptions()
        # options.add_argument('--headless=new')
        options.add_argument('headless')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(options=options, service=service)

        # Open the listafirme.ro search page
        driver.get(url="https://www.listafirme.ro/search.asp")

        # Perform any further interactions with the page as needed

        search_name = driver.find_element(By.NAME, 'searchfor')

        # print(search_name)

        search_name.send_keys(nume)

        print('----------------------')
        print(driver.window_handles)
        button_xpath = driver.find_element(By.XPATH, '//button[text()="Caută"]')
        button_xpath.click()
        # time.sleep(2)

        button_row = driver.find_element(By.CLASS_NAME, 'clickable-row')
        button_row.click()

        time.sleep(0.5)

        all_handles = driver.window_handles

        new_tab_handle = all_handles[-1]
        driver.switch_to.window(new_tab_handle)

        CUI = driver.find_element(By.CSS_SELECTOR, 'tbody tr:nth-child(3) > :nth-child(2)')
        temp = CUI.text
        driver.quit()
        print('-'*10)
        print(temp)
        return temp
    except:
        return ''

def anaf(name):
    api_url = 'https://webservicesp.anaf.ro/PlatitorTvaRest/api/v6/ws/tva'
    now = datetime.now()

    current_time = now.strftime("%Y-%m-%d")
    data = requests.post(api_url, data=json.dumps([{'cui': scrape(name), 'data' : f"{current_time}"}]), headers={'Content-Type': 'application/json'})

    if data is not None and data.status_code == 200 and 'Request Rejected' not in data.text:
        print(data.text)
        data_json = json.loads(data.text)

        msg = ['scopTVA' + ' ' + data_json['found'][0]['mesaj_ScpTVA'], 'stare' + ' ' + data_json['found'][0]['stare_inregistrare']]

        return ','.join(msg)

    return ''

