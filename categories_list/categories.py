#!/usr/bin/python3

import lxml.html as html
import csv


def get_categories(url):
    page = html.parse(url)
    root = page.getroot()
    table = root.find_class("all-api-categories")[0].getchildren()[0]
    categories = []
    for i in table.getchildren():
        name = i.getchildren()[0].getchildren()[0].find(".//a").text_content()
        href = i.getchildren()[0].find(".//a").get("href")
        count = int(i.getchildren()[1].find(".//span").text_content().strip('()').replace(",", ""))
        categories.append([name, href, count])
    return categories

url = "http://www.programmableweb.com/category"
result = get_categories(url)
for i in range(1, 8):
    categories = get_categories(url+"?page="+str(i))
    result.extend(categories)

writer = csv.writer(open('categories.csv', 'w'), delimiter=',')
for i in result:
    writer.writerow(i)
