#!usr/bin/python3

from rdflib import Namespace, RDF
import numpy as np

ns = dict(api_network=Namespace("http://deepweb.ut.ee/ontologies/api-network#"),
          cat=Namespace("http://www.programmableweb.com/category/"),
          rdf=RDF, gr=Namespace("http://purl.org/goodrelations/v1#"),
          pw_api=Namespace("http://www.programmableweb.com/api/"),
          xsd=Namespace("http://www.w3.org/2001/XMLSchema#"))


def cats_of_mashup(mashup, g):
    rows = g.query("""SELECT ?t WHERE {
        <%s> api_network:tag ?t .}""" % mashup, initNs=ns)
    return [t["?t"] for t in rows.bindings]  # query select tags by Mashup name


def cos(S, mashup2, g):
    S2 = cats_of_mashup(mashup2, g)
    return len(set(S).intersection(S2))/((len(S)*len(S2))**(1/2.0))


def cosine(mashups2, mashup, g):
    S = cats_of_mashup(mashup, g)
    return np.max([cos(S, m2, g) for m2 in mashups2])  # score / len(mashups2)


def partly_relevance(service, mashup, g):  # partial relevance means that given api was used by another mashup with same categories
    r = g.query("""SELECT ?m {<%s> api_network:tag ?t .
                ?m api_network:tag ?t .
                ?m gr:include <%s> .
                }""" % (mashup, service),
                initNs=ns)
    if len(r) == 0:
        return 0
    else:
        mashups2 = [t["?m"] for t in r.bindings]
        return cosine(mashups2, mashup, g)


# consider https://en.wikipedia.org/wiki/Cosine_similarity
def is_relevant(service, actual, mashup, g):
    if service in actual:
        return 1
    else:
        return partly_relevance(service, mashup, g)


def average_precision(actual, predicted, k, mashup, g):
    score = 0.0
    num_hits = 0.0
    if len(predicted) > k:
        predicted = predicted[:k]
    for i, p in enumerate(predicted):
        relevance = is_relevant(p, actual, mashup, g)
        # print(p, " ", relevance)
        if relevance != 0:
            num_hits += relevance  # 1.0
            # print(num_hits)
            score += num_hits*relevance / (i + 1)
            # print(score)
    if not actual:
        return 0.0
    # m = min(len(actual), len(predicted))
    # print(m)
    return score / k
