#!usr/bin/python3

from rdflib import Namespace, RDF
from pandas import Series
import numpy as np
import operator

ns = dict(api_network=Namespace("http://deepweb.ut.ee/ontologies/api-network#"),
          cat=Namespace("http://www.programmableweb.com/category/"),
          rdf=RDF, gr=Namespace("http://purl.org/goodrelations/v1#"),
          pw_api=Namespace("http://www.programmableweb.com/api/"),
          xsd=Namespace("http://www.w3.org/2001/XMLSchema#"))


def compose_query(g, mashup):  # return tuple of number of required services,list of required categories and registration date
    rows = g.query("""SELECT ?t WHERE {
        <%s> api_network:tag ?t .}""" % mashup, initNs=ns)  # query select tags by Mashup name
    categories = [t["?t"] for t in rows.bindings]
    rows = g.query("""SELECT ?t WHERE {
        <%s> gr:include ?t .}""" % mashup, initNs=ns)
    # k = len(rows)
    rows = g.query("""SELECT ?d WHERE {
        <%s> api_network:registrationDate ?d .
        }""" % mashup, initNs=ns)
    reg_date = [t["?d"].toPython() for t in rows.bindings][0]
    rows = g.query("""SELECT ?s WHERE {
        <%s> ?p api_network:Mashup .
        <%s> gr:include ?s .}""" % (mashup, mashup), initNs=ns)  # query select tags by Mashup name
    involved_services = [t["?s"] for t in rows.bindings]
    return {"categories": categories, "reg_date": reg_date,
            "services": involved_services}


def union_of_two_lists(first_list, second_list):
    in_first = set(first_list)
    in_second = set(second_list)
    in_second_but_not_in_first = in_second - in_first
    result = first_list + list(in_second_but_not_in_first)
    return result


def get_categories(services, g):
    primary_categories = []
    secondary_categories = []
    for service in services:
        rows = g.query("""SELECT ?c WHERE {
            <%s> api_network:primaryCategory ?c .}""" % service, initNs=ns)
        p_cats = [t["?c"] for t in rows.bindings]
        primary_categories = primary_categories + list(set(p_cats) - set(primary_categories))
        rows2 = g.query("""SELECT ?c WHERE {
            <%s> api_network:secondaryCategory ?c .}""" % service, initNs=ns)
        s_cats = [t["?c"] for t in rows2.bindings]
        secondary_categories = secondary_categories + list(set(s_cats) - set(secondary_categories))
    return (primary_categories, secondary_categories)


def get_intersections(services, S, g):
    services_categories = get_categories(services, g)
    primary_intersection = [val for val in services_categories[0] if val in S]
    secondary_intersection = [val for val in services_categories[1] if val in S]
    return (primary_intersection, secondary_intersection)


def sc(services, S, g):
    # services_categories = get_categories(services)
    # primary_intersection = [val for val in services_categories[0] if val in S]
    # secondary_intersection = [val for val in services_categories[1] if val in S]
    intersections = get_intersections(services, S, g)
    return (len(intersections[0])+0.3*len(intersections[1]))/len(S)  # number of requested categories in service is devided by size of requested categories


def re(services, S, g):
    # services_categories = get_categories(services)
    # primary_intersection = [val for val in services_categories[0] if val in S]
    # secondary_intersection = [val for val in services_categories[1] if val in S]
    # intersection = [val for val in services_categories if val in S]
    intersections = get_intersections(services, S, g)
    categories = get_categories(services, g)
    provided_categories = union_of_two_lists(categories[0], categories[1])
    return (len(intersections[0])+0.3*len(intersections[1]))/len(provided_categories)  # number of requested categories in service is devided by size of provided categories


def activation_time_mapping_function(n_days):
    x = np.arange(0., 3., 0.001)  # define range
    y = np.exp(4*(-x))  # define exponential function, b=4 just an example
    return y[n_days]


def dt_for_single_service(service, g):
    rows = g.query("""SELECT ?d WHERE {
                <%s> api_network:registrationDate ?d .
                }""" % service, initNs=ns)
    reg_date = [t["?d"].toPython() for t in rows.bindings][0]
    rows = g.query("""SELECT ?d1 WHERE {
                ?m gr:include <%s> .
                ?m api_network:registrationDate ?d1 .
                }""" % service, initNs=ns)
    mashup_reg_date = [t["?d1"].toPython() for t in rows.bindings]
    if not mashup_reg_date:
        activation_time = 0  # if service has not been activated, then activation_time is 0
    else:
        mrd = Series(mashup_reg_date)  # turn list to Series
        first_mashup_registration_date = mrd[mrd >= reg_date].min()  # get rid of negative registrations
        try:
            activation_time = first_mashup_registration_date - reg_date
            activation_time = activation_time.days  # convert from timedelta to days
            activation_time = activation_time_mapping_function(activation_time)  # mapping from days to score
        except:
            activation_time = 0
    return activation_time


def dt(services, g):
    result = 0
    for service in services:
        result = result + dt_for_single_service(service, g)
    return result


def score(g, services, S, lambda1, lambda2, lambda3):
    return [lambda1*sc(services, S, g), lambda2*re(services, S, g), lambda3*dt(services, g)]


# TODO add filter by date
def get_services_by_category(category, reg_date, g):
    rows = g.query("""SELECT DISTINCT ?s WHERE {?s ?p api_network:API .
                ?s api_network:primaryCategory|api_network:secondaryCategory cat:%s .
                ?m ?p api_network:Mashup .
                ?m gr:include ?s .
                }""" % category, initNs=ns)
    return [t["?s"] for t in rows.bindings]


def candidate_set(query, g):
    set_of_services = []
    for category in query["categories"]:
        category = category.toPython().replace("http://www.programmableweb.com/category/", "")
        services = get_services_by_category(category, query["reg_date"], g)
        set_of_services = set_of_services + list(set(services) - set(set_of_services))
    return set_of_services


# main experiment
def compose_B_table(s, I, g, S, lambda1, lambda2, lambda3):
    temp_I = I + [s]
    curr_score = score(g, temp_I, S, lambda1, lambda2, lambda3)
    return (temp_I, sum(curr_score))


def Greedy(g, S, M, k, lambda1, lambda2, lambda3):
    I = []  # recommendation set of services
    B = 0  # current score
    for i in range(k):
        B_table = [compose_B_table(s, I, g, S, lambda1, lambda2, lambda3) for s in M]
        I, B = max(B_table, key=operator.itemgetter(1))
        M = [x for x in M if x not in I]  # delete added elements from candidate set
    return (I, B)
