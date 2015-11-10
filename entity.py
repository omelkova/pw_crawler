#!/usr/bin/python3


from rdflib import Namespace, RDF, Literal, URIRef, XSD
import re
import lxml.html as html
import urllib.request
from datetime import datetime
import csv
import logging


def add_categories_to_graph(graph):
    with open('parse_categories/categories.csv') as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        for row in readCSV:
            category = URIRef(Entity.pw+row[1])
            name = row[0]
            graph.add((category, RDF.type, Entity.skos.Concept))
            graph.add((category, Entity.rdfs.label, Literal(name, lang='en')))
    return graph


def get_root_dataset_entity(graph):
    return list(graph.subjects(RDF.type, Entity.localNS.Dataset))[0]


def add_attachment_to_dataset(entity, graph):
    root = get_root_dataset_entity(graph)
    graph.add((root, Entity.gr.include, entity.get_root_entity()))


def add_creation_date(entity, date, graph):
    graph.add((entity.get_root_entity(), Entity.localNS.registrationDate,
               Literal(datetime.strptime(date, "%m.%d.%Y").date())))


def merge_two_dicts(d1, d2):
    d3 = {}
    for k, v in d1.items():
        k1 = d1[k]
        try:
            k2 = d2[k]
        except:
            k2 = []
        ret = list(set(k1 + k2))
        d3[k] = ret
    d3.update(d2)
    return d3


def get_next_page(page):
    try:
        e1 = html.parse(page).getroot().find_class('pager')[0].find(".//a")
        href = "http://www.programmableweb.com/" + e1.get("href")
        return href
    except:
        return None


def parse_page_mashups(page):
    def merge_two_dicts(d1, d2):
        d3 = d1.copy()
        d3.update(d2)
        return d3

    def get_next_mashup_page(page):
        try:
            e1 = html.parse(page).xpath(".//ul[@class='pagination']")
            href = e1[0].find(".//a[@title='Go to next page']").get("href")
            return "http://www.programmableweb.com" + href
        except:
            return None

    def get_mashups_content(page):
        a = html.parse(page).xpath(".//table")
        table = a[0].getchildren()[1]
        developers = {}
        for i in table.getchildren():
            name = i.getchildren()[0].find(".//a").get("href")
            date = i.getchildren()[3].text_content().strip()
            developers[name] = date
        return developers

    try:
        next_page = get_next_mashup_page(page)
        if next_page is not None:
            return merge_two_dicts(get_mashups_content(page), parse_page_mashups(next_page))
        else:
            return get_mashups_content(page)
    except:
        return {}


def parse_page_devs(page):
    def get_developers_content(page):
        e1 = html.parse(page).xpath(".//div[@id='developers']")
        table = e1[0].findall(".//table")[0].getchildren()[1]
        developers = {}
        for i in table.getchildren():
            key = i.getchildren()[0].findall('a')[1].get('href')
            value = i.getchildren()[2].findall('a').pop().get('href')
            if key in developers:
                developers[key].append(value)
            else:
                developers[key] = [value]
        return developers

    try:
        next_page = get_next_page(page)
        if next_page is not None:
            return merge_two_dicts(get_developers_content(page), parse_page_devs(next_page))
        else:
            return get_developers_content(page)
    except:
        return {}


def parse_page(page):
    def get_followers_content(page):
        # print(page)
        # logging.info("Parsing page: %s", page)
        e1 = html.parse(page).xpath(".//div[@id='followers']")
        table = e1[0].findall(".//table")[0].getchildren()[1]
        followers = []
        for i in table.getchildren():
            followers.append(i[1].find(".//a").get("href"))
        return followers
    try:
        next_page = get_next_page(page)
        # print(next_page)
        # logging.info("Next page is %s", next_page)
        if next_page is not None:
            return get_followers_content(page) + parse_page(next_page)
        else:
            return get_followers_content(page)
    except:
        return []


def bind_namespaces_to_graph(graph):
    graph.bind("api-network", Entity.localNS)
    graph.bind("dcterms", Entity.dcterms)
    graph.bind("sioc", Entity.sioc)
    graph.bind("foaf", Entity.foaf)
    graph.bind("gr", Entity.gr)
    graph.bind("rdfs", Entity.rdfs)
    graph.bind("skos", Entity.skos)
    return graph


def bind_root_node_to_graph(graph, name):
    root = Entity.localNS.term(name)
    graph.add((root, RDF.type, Entity.localNS.Dataset))
    graph.add((root, Entity.dcterms.created, Literal(datetime.utcnow())))
    graph.add((root, Entity.rdfs.label, Literal("Programmable Web dataset", lang='en')))
    graph.add((root, Entity.dcterms.title, Literal("Programmable Web dataset", lang='en')))
    # graph.add((root, Entity.dcterms.description, Literal(" ", datatype=XSD.string, lang='en')))
    creator = Entity.localNS.omelkova
    graph.add((creator, RDF.type, Entity.foaf.Person))
    graph.add((creator, Entity.foaf.name, Literal("Svetlana Omelkova")))
    graph.add((creator, Entity.foaf.mbox, Literal("svetlana.omelkova@gmail.com")))
    graph.add((creator, Entity.foaf.homepage, URIRef("http://kodu.ut.ee/~vorotnik/")))
    graph.add((root, Entity.dcterms.creator, creator))
    return graph
    #  add other information about the dataset

_invalid_uri_chars = '<>" {}|\\^`'


def _is_valid_uri(uri):
    for c in _invalid_uri_chars:
        if c in uri:
            return False
    return True


def prop_obj_mapping(key, value):  # key is a name of a field, value - xml elem
    prop = prop_mapping(key)  # uri of the property
    obj_arr = obj_mapping(value, key)
    return [prop, obj_arr]


def prop_mapping(prop_str):
    ns = Entity.__dict__[Entity.prop_mapping_dict[prop_str][0]]
    uri = ns.term(Entity.prop_mapping_dict[prop_str][1])
    return uri


def obj_mapping(obj, prop):  # obj_str is an element
    if prop == "Related APIs" or prop == "Primary Category" or prop == "Secondary Categories" or prop == "Tags":
        arr = obj.xpath(".//@href")
        return [URIRef(Entity.pw+i) for i in arr]
    elif len(obj.getchildren()) <= 1:
        obj = obj.text_content()
        if Entity.url_pattern.match(obj) and _is_valid_uri(obj):
            return [URIRef(obj)]
        else:
            return [Literal(obj)]
    else:
        arr = obj.xpath(".//text()")
        arr = [x for x in arr if x != ", "]
        return [Literal(i) for i in arr]


class Entity(object):
    url_pattern = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d-{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    prop_mapping_dict = {
        "API Provider": ["localNS", "hasProvider"],
        "API Endpoint": ["localNS", "hasEndpoint"],
        "API Homepage": ["localNS", "commentUrl"],
        "Primary Category": ["localNS", "primaryCategory"],
        "Secondary Categories": ["localNS", "secondaryCategory"],
        "Protocol / Formats": ["localNS", "protocol"],
        "Other options": ["localNS", "protocol"],
        "SSL Support": ["localNS", "ssl"],
        "Developer Support": ["localNS", "support"],
        "Authentication Mode": ["localNS",  "authentication"],
        "Related APIs": ["gr", "include"],
        "Tags": ["localNS", "tag"],
        "URL": ["localNS", "hasEndpoint"],
        "Company": ["localNS", "hasProvider"],
        "Mashup/App Type": ["localNS", "type"],
        "API Forum": ["localNS", "forum"]
        }

    localNS = Namespace("http://deepweb.ut.ee/ontologies/api-network#")
    pw = "http://www.programmableweb.com"
    dcterms = Namespace("http://purl.org/dc/terms/")
    sioc = Namespace("http://rdfs.org/sioc/ns#")
    foaf = Namespace("http://xmlns.com/foaf/0.1/")
    gr = Namespace("http://purl.org/goodrelations/v1#")
    rdfs = Namespace("http://www.w3.org/2000/01/rdf-schema#")
    skos = Namespace("http://www.w3.org/2004/02/skos/core#")

    def is_deprecated(self, root):
        try:
            if "deprecated" not in root.find_class('deprecated')[0].text_content():
                return False
            else:
                return True
        except:
            return False

    # to rdf mapping
    def add_specs(self, graph, spec_dict, entity):
        for key in spec_dict:
            # print(key)
            if key in Entity.prop_mapping_dict:
                # print(key)
                prop, obj_arr = prop_obj_mapping(key, spec_dict[key])
                for obj in obj_arr:
                    graph.add((entity, prop, obj))
        return graph

    def create_root_entity(self):
        return self.pw.term(self.info["abbr"])

    # web page parsing
    def initialization(self):
        logging.info("Initializing entity %s", self.domain)
        page = html.parse(self.domain)  # initialization
        root = page.getroot()
        return root

    def get_intro(self, root):
        d = root.find_class('intro').pop()
        description = d.getchildren()[1].text_content()
        return description.strip()

    def get_specs(self, root):
        e = root.find_class('specs').pop()
        specs = {}
        for i in e.getchildren()[1:]:
            specs[i.getchildren()[0].text_content()] = \
                i.getchildren()[1]  # .text_content()
        return specs

    def get_followers(self):
        page = self.domain + "/followers"
        return parse_page(page)

    @staticmethod
    def factory(type, name):
        if type == "Service":
            return Service(name)
        if type == "User":
            return User(name)
        if type == "Mashup":
            return Mashup(name)

    # interface
    def __init__(self):
        pass

    def parse(self):
        root = self.initialization()
        description = self.get_intro(root)
        specs = self.get_specs(root)
        followers = self.get_followers()
        deprecated = self.is_deprecated(root)
        self.info = {"abbr": self.name, "DESC": description,
                     "SPECS": specs, "FOLLOWERS": followers,
                     "IS_DEPRECATED": deprecated}  # form a dict
        self.entity = self.create_root_entity()
        return (self.info)

    def get_root_entity(self):
        return self.entity

    def tordf(self, graph):
        graph.add((self.entity, RDF.type, self.entity_type))
        graph.add((self.entity, Entity.dcterms.description,
                   Literal(self.info["DESC"], lang='en')))
        if self.info["IS_DEPRECATED"]:
            graph.add((self.entity, Entity.localNS.isDeprecated,
                       Literal('true', datatype=XSD.boolean)))
        graph = self.add_specs(graph, self.info["SPECS"], self.entity)
        graph = self.add_followers_to_rdf(graph)
        return graph

    # redundant with add_developer
    def add_followers_to_rdf(self, graph):
        for i in self.info["FOLLOWERS"]:
            follower_name = i.replace("/profile/", "")
            follower = User.pw.term(follower_name)
            if (follower, None, None) not in graph:
                try:
                    user = Entity.factory("User", follower_name)
                    graph = user.tordf(graph)
                except:
                    pass
            graph.add((follower, Entity.sioc.follows, URIRef(self.domain)))
        return graph


class Service(Entity):
    pw = Namespace(Entity.pw+"/api/")
    entity_type = Entity.localNS.API

    def __init__(self, service_name):
        self.name = service_name
        self.domain = 'http://www.programmableweb.com/api/{}'\
            .format(service_name)
        self.parse()

    def parse(self):
        root = self.initialization()
        description = self.get_intro(root)
        specs = self.get_specs(root)
        followers = self.get_followers()
        developers = self.get_developers()
        mashups = self.get_mashups(root)
        deprecated = self.is_deprecated(root)
        self.info = {"abbr": self.name, "DESC": description,
                     "SPECS": specs, "FOLLOWERS": followers,
                     "DEVELOPERS": developers, "MASHUPS": mashups,
                     "IS_DEPRECATED": deprecated}  # form a dict
        self.entity = self.create_root_entity()
        return (self.info)

    def get_developers(self):
        page = self.domain + "/developers"
        return parse_page_devs(page)

    def get_mashups(self, root):
        mashups_url = self.get_mashups_list_url(root)
        return parse_page_mashups(mashups_url)

    def get_mashups_list_url(self, root):
        a = root.find(".//section[@id='block-views-api-mashups-new-list-top']")
        href = a.xpath('.//a[text()="/View all"]')[0].get("href")
        return "http://www.programmableweb.com" + href

    def tordf(self, graph):
        graph = Entity.tordf(self, graph)
        graph = self.add_developers(graph)
        graph = self.add_mashups(graph)
        return graph

    def add_developers(self, graph):
        dev_dict = self.info["DEVELOPERS"]
        for dev in dev_dict:
            dev_name = dev.replace("/profile/", "")
            developer = User.pw.term(dev_name)
            if (developer, None, None) not in graph:
                try:
                    user = Entity.factory("User", dev_name)
                    graph = user.tordf(graph)
                except:
                    pass
            graph = self.add_developers_content(graph, developer, dev_dict[dev])
        return graph

    def add_developers_content(self, graph, developer, arr_content):
        for mashup in arr_content:
            graph.add((developer, Entity.gr.offer, Namespace(Entity.pw).term(mashup)))
        return graph

    def add_mashups(self, graph):
        mashups_dict = self.info["MASHUPS"]
        for mash in mashups_dict:
            mashup_name = mash.replace("/mashup/", "")
            mashup = Mashup.pw.term(mashup_name)
            if (mashup, None, None) not in graph:
                try:
                    mashup_entity = Entity.factory("Mashup", mashup_name)
                    graph = mashup_entity.tordf(graph)
                except:
                    pass
            graph.add((mashup, Entity.localNS.registrationDate,
                       Literal(datetime.strptime(mashups_dict[mash], "%m.%d.%Y").date())))
        return graph


class User(Entity):
    pw = Namespace(Entity.pw+"/profile/")

    def __init__(self, user_name):
        self.user_name = user_name
        self.domain = 'https://www.programmableweb.com/profile/{}'\
            .format(user_name)
        self.parse()

    def parse(self):
        root = self.initialization()
        # real_name = self.get_about(root)
        watchlist = self.get_watchlist(root)
        registered_content = self.get_registered_content(root)
        self.info = {"abbr": self.user_name, "WATCHLIST": watchlist,
                     "REGISTERED": registered_content}

    def initialization(self):
        # print(self.domain)
        logging.info("Initializing user %s", self.domain)
        page = html.parse(urllib.request.urlopen(self.domain))
        root = page.getroot()
        return root

    def get_about(self, root):
        main = root.find_class('about').pop()
        real_name = main.getchildren()[2].getchildren()[1].text_content()
        return real_name

    def get_registered_content(self, root):
        try:
            main = root.find_class('mashups-table')[0]
            table = main.findall(".//table").pop()
            table_content = table.findall(".//tbody").pop()
            content = []
            for i in table_content.getchildren():
                content.append(i.find('.//a').get('href'))
            return content
        except:
            return []

    def get_watchlist(self, root):
        try:
            main = root.find_class('watchlist-table').pop()
            table = main.findall(".//table")
            watchlist = []
            if table:
                table_content = table.pop().findall(".//tbody").pop()
                for i in table_content.getchildren():
                    item_list = i[1].findall('a')
                    if item_list:
                        watchlist.append(item_list[0].get("href"))
            return watchlist
        except:
            return []

    def tordf(self, graph):
        self.user = self.create_root_entity()
        graph.add((self.user, RDF.type, Entity.foaf.OnlineAccount))
        graph = self.add_watchlist(graph, self.info["WATCHLIST"], self.user)
        graph = self.add_registered_content(graph, self.info["REGISTERED"], self.user)
        return graph

    def add_registered_content(self, graph, cont_arr, entity):
        for i in cont_arr:
            graph.add((entity, Entity.gr.offer, URIRef(Entity.pw+i)))
        return graph

    def add_watchlist(self, graph, wl_dict, entity):
        if wl_dict:
            for i in wl_dict:
                graph.add((entity, Entity.sioc.follows, URIRef(Entity.pw+i)))
        return graph


class Mashup(Entity):
    pw = Namespace(Entity.pw+"/mashup/")
    entity_type = Entity.localNS.Mashup

    def __init__(self, mashup_name):
        self.name = mashup_name
        self.domain = 'http://www.programmableweb.com/mashup/{}' \
            .format(mashup_name)
        self.parse()
