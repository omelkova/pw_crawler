#!/usr/bin/python3


from lxml import etree
import csv
import lxml.html as html
import logging


entity = "mashup"
categories_source = '../categories_list/categories.csv'
output_folder = 'categories_mashups/'


def stringify_children(node):
    from lxml.etree import tostring
    from itertools import chain
    parts = ([node.text] +
             list(chain(*([c.text, tostring(c), c.tail] for c in node.getchildren()))) +
             [node.tail])
    return ''.join(filter(None, parts))


def parse_given_category(page):
    def parse_page(page_name):
        parser = etree.HTMLParser()
        tree = etree.parse(page_name, parser=parser)
        root = tree.getroot()
        e1 = root.find(".//div[@id='"+entity+"']")
        table = e1.find(".//table")
        content = table.getchildren()[1]
        result = []
        for line in content.getchildren():
            name = line.getchildren()[0].find(".//a").get('href')
            date = stringify_children(line.getchildren()[3]).strip()
            result.append([name, date])
        return result

    def get_next_page(page):
        try:
            href = html.parse(page).getroot().find_class("pager")[0].find(".//a").get("href")
            next_page = "http://www.programmableweb.com" + href
            return next_page
        except:
            return None

    logging.info("Parsing page %s", page)
    print("Parsing page", page)
    next_page = get_next_page(page)
    if next_page is not None:
        return parse_page(page) + parse_given_category(next_page)
    else:
        return parse_page(page)


def to_csv(arr, name):
    file_name = output_folder + name[10:] + ".csv"
    logging.info("Creating csv file with name %s", file_name)
    csv_writer = csv.writer(open(file_name, 'w'), delimiter=',')
    for i in arr:
        csv_writer.writerow(i)


def main():
    print("Script started")
    with open(categories_source) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        for row in readCSV:
            name = row[1]
            url = "http://www.programmableweb.com"+name+"/"+entity
            logging.info("Parsing %s category", name)
            print("Parsing category %s", name)
            try:
                result = parse_given_category(url)
                to_csv(result, name)
            except:
                logging.error('Problems with %s', name, exc_info=True)


if __name__ == '__main__':
    logging.basicConfig(filename='categories_catalog.log', format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Script started")
    main()
