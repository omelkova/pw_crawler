#!usr/bin/python3

from rdflib import Graph, RDF, Namespace
from pandas import DataFrame
import datetime
import experiment as exp
import validation as val
import numpy as np
import pandas as pd


ns = dict(api_network=Namespace("http://deepweb.ut.ee/ontologies/api-network#"),
          cat=Namespace("http://www.programmableweb.com/category/"),
          rdf=RDF, gr=Namespace("http://purl.org/goodrelations/v1#"),
          pw_api=Namespace("http://www.programmableweb.com/api/"),
          xsd=Namespace("http://www.w3.org/2001/XMLSchema#"))


def single_experiment(mashup, g, range_tuple, df_weights):
    user_query = exp.compose_query(g, mashup)
    # M = exp.candidate_set(user_query, g)  # set of candidate services
    M = exp.candidate_set_all_activated(g)  # set of candidate services, all activated
    S = user_query["categories"]  # set of requested tags
    actual = user_query["services"]
    k = min(range_tuple[1]-1, len(M))
    result = exp.Greedy(g, S, M, k, 1, 0, 1, df_weights)
    array_of_avg_precisions = []
    for i in range(range_tuple[0], k+1):
        predicted = result[0][:i]
        array_of_avg_precisions.append(val.average_precision(actual, predicted, i, mashup, g))  # compute average precision
    diff = range_tuple[1] - 1 - len(array_of_avg_precisions)
    if diff == 0:
        return array_of_avg_precisions
    else:
        return np.append(array_of_avg_precisions, np.repeat(np.nan, diff)).tolist()


def mashups_for_experiment(g):
    rows = g.query("""SELECT ?m ?d WHERE {?m ?p api_network:Mashup .
                  ?m api_network:registrationDate ?d .}""", initNs=ns)
    mashup_regs = DataFrame()
    mashup_regs["Mashup"] = [t["?m"].toPython() for t in rows.bindings]
    mashup_regs["Registration"] = [t["?d"].toPython() for t in rows.bindings]
    mashup_for_experiment = mashup_regs[mashup_regs["Registration"] > datetime.date(2015, 6, 13)]["Mashup"]  # select 65 mashups
    return mashup_for_experiment


def experiment():
    g = Graph()
    g.parse("../graph/experiment_graph.ttl", format="turtle")
    mashup_for_experiment = mashups_for_experiment(g)
    average_precision_frame = DataFrame()
    range_tuple = (1, 11)
    df_weights = pd.read_csv("weighted_diffusion_matrix.csv", index_col=0)
    for mashup in mashup_for_experiment:
        print(mashup)
        arr_of_precisions = [mashup] + single_experiment(mashup, g, range_tuple, df_weights)
        df = DataFrame([arr_of_precisions], columns=["Mashup"]+["k = %s" % k for k in range(*range_tuple)])
        average_precision_frame = average_precision_frame.append(df, ignore_index=True)
    average_precision_frame.to_csv("1_0_1_with_weights_result.csv")


def main():
    experiment()


if __name__ == '__main__':
    main()
