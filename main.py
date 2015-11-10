#!/usr/bin/python3


import entity as e
from entity import Entity, bind_namespaces_to_graph, bind_root_node_to_graph
from rdflib import Graph, Namespace
import csv
import logging
import os


csv_dir = 'categories'
experiment_name = 'adding_mashups'
output_graph = 'graph/experiment_graph.ttl'
new_experiment = False  # if true then new graph will be created and initialized
# if false, then old file with specified name will be readed and
# processed


def initialize_graph(name):
    graph = Graph()
    graph = bind_namespaces_to_graph(graph)
    graph = bind_root_node_to_graph(graph, name)
    graph = e.add_categories_to_graph(graph)
    return graph


def experiment(name):
    if new_experiment:
        graph = initialize_graph(name)
        logging.info("New graph has been initialized")
    else:
        graph = open_graph(output_graph)
        logging.info("Graph %s has been processed", output_graph)
    iterate_directory(csv_dir, graph, name)


def iterate_directory(csv_dir, graph, experiment_name):
    for subdir, dirs, files in os.walk(csv_dir):
        for f in files:
            if f.endswith(".csv"):
                file_name = os.path.join(subdir, f)
                graph = process_csv(file_name, graph)
                graph.serialize(destination=output_graph, format='turtle')
                logging.info("Graph has been serialized after processing file %s", file_name)
                os.remove(file_name)
                logging.info("File %s has been removed", file_name)


def service_is_in_graph(service_name, graph):
    # service = Namespace("http://www.programmableweb.com/api/").term(service_name)
    service = Namespace("http://www.programmableweb.com/mashup/").term(service_name)
    if (service, None, None) in graph:
        return True
    else:
        return False


def process_csv(file_name, graph):
    logging.info("Processing file: %s", file_name)
    with open(file_name) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        for row in readCSV:
            # service_name = row[0].replace("/api/", "")
            service_name = row[0].replace("/mashup/", "")
            logging.info("Processing service %s", service_name)
            date = row[1]
            if not service_is_in_graph(service_name, graph):
                try:
                    # entity = Entity.factory("Service", service_name)
                    entity = Entity.factory("Mashup", service_name)
                    graph = entity.tordf(graph)
                    # e.add_attachment_to_dataset(entity, graph)
                    e.add_creation_date(entity, date, graph)
                except:
                    logging.error("Something wrong with the service %s", service_name, exc_info=True)
            else:
                logging.info("Service %s is already in a graph", service_name)
    return graph


def open_graph(file_name, format="turtle"):
    graph = Graph()
    graph.parse(file_name, format=format)
    return graph


def test():
    g = Graph()
    entity = Entity.factory("Service", "google-maps")
    g = entity.tordf(g)
    g.serialize(destination="test.ttl", format='turtle')


def main():
    experiment(experiment_name)


if __name__ == '__main__':
    logging.basicConfig(filename=experiment_name+".log", level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Experiment started with name %s", experiment_name)
    main()
