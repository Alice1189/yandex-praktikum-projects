#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import codecs
import base64
import re

ipynb_names = ['airline-analytics.ipynb',
               'airline-analytics_(parser-SQL).ipynb',
               'communications-statistical-analysis.ipynb',
               'credit-scoring-preprocessing.ipynb',
               'e-commerce-a-b-testing.ipynb',
               'e-commerce-games.ipynb',
               'food-shopping-app.ipynb',
               'outflow-fitness-club.ipynb',
               'product-assortment.ipynb',
               'real-estate-eda.ipynb',
               'restaurants-visualization.ipynb',
               'yandex-afisha-business-analysis.ipynb']


# Структура:  
# в одной папке лежат все проекты и папка с изображениями (images), в которую
# сохранялись графики при выполнении проектов, и из которой же берутся
# графики для отображения в ячейках markdown

if not os.path.exists('new'):
    os.makedirs('new')

# проходимся по всем файлам ipynb
for nb_file in ipynb_names:
    # открываем файл, читаем
    fin = codecs.open(os.path.abspath(nb_file), encoding='utf-8', mode='r')
    s = fin.read()
    soup = BeautifulSoup(s)
    fin.close()
    # создаём пустой файл ipynb
    fout = codecs.open(os.path.abspath('new/'+nb_file), encoding='utf-8', mode='w')
    # находим все картинки по тегу img
    images = soup.findAll('img')
    # создаём словарь соответствия <что заменить>:<на что заменить>
    d = {}
    for img in images:
        # проверяем откуда брали картинки, чтобы найти их
        img_path = img['src'][2:len(img['src'])-2]
        if '../images/' in img['src']:
            img_path = img['src'][5:len(img['src'])-2]
        # по пути из src берём картинку и генерируем код base64
        encoded = str(base64.b64encode(open(img_path, "rb").read()))
        l = len(encoded)
        # пишем в словарь <старый src>:<новый src>
        d[img['src']] = 'data:image/png;base64,'+encoded[2:l-1]
        # меняем содержимое исходного файла
        new_s = s.replace('src = '+img['src'], 'src = \\"'+d[img['src']]+'\\"')
        s = new_s
    images = re.findall(r'\!\[\]\([^\)]+\)', s)
    # создаём словарь соответствия <что заменить>:<на что заменить>
    d = {}
    for img in images:
        # для каждой картинки определяем путь
        img_path = img[4:len(img)-1]
        # по пути из src берём картинку и генерируем код base64
        encoded = str(base64.b64encode(open(img_path, "rb").read()))
        l = len(encoded)
        # пишем в словарь <старый src>:<новый src>
        d[img] = '<img src = \\"data:image/png;base64,'+encoded[2:l-1]+'\\" />'
        # меняем содержимое исходного файла
        new_s = s.replace(img, d[img])
        s = new_s
    # пишем в новый файл преобразованное содержимое исходного файла
    fout.write(s)
    # закрываем файлы
    fout.close()

# После создания новых файлов в папке 'new' нужно либо заменить пути к датасетам,
# либо переместить новые файлы на место старых.