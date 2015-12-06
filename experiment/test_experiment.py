#!usr/bin/python3

import unittest
import experiment as exp
from rdflib import Graph
import datetime
import time
# import rdflib


class Test(unittest.TestCase):

    def setUp(self):
        self.g = Graph()
        self.g.parse("../graph/for_test_graph.ttl", format="turtle")
        self.mashup = "http://www.programmableweb.com/mashup/fast-quick-online-translator"
        self.query = exp.compose_query(self.g, self.mashup)
        self.candidate_set = exp.candidate_set(self.query, self.g)

    def tearDown(self):
        self.g.close()

    def test_query_creation(self):
        self.assertEqual(len(self.query["services"]), 2)
        self.assertEqual(len(self.query["categories"]), 2)
        self.assertEqual(self.query["reg_date"], datetime.date(2010, 4, 26))

    def test_union_of_two_lists(self):
        A = ["A", "B", "C"]
        B = ["C", "B"]
        self.assertEqual(exp.union_of_two_lists(A, B), ["A", "B", "C"])

    def test_score_computation(self):
        services = ["http://www.programmableweb.com/api/lingo24-translation"]
        score = exp.score(self.g, services, self.query["categories"], 1, 1, 1)
        self.assertEqual(sum(score), 0.75)

    def test_candidate_set_creation(self):
        self.assertEqual(len(self.candidate_set), 9)

    def test_recommendation_algorithm(self):
        expected_recommendation = [rdflib.term.URIRef('http://www.programmableweb.com/api/google-ajax-language'),
                                   rdflib.term.URIRef('http://www.programmableweb.com/api/google-translate')]
        self.assertEqual(exp.Greedy(self.g, self.query["categories"],
                                    self.candidate_set, len(self.query["services"]), 1, 1, 1)[0], expected_recommendation)

    # def test_optimizedGreedy(self):
    #    normal_recommendation = exp.Greedy(self.g, self.query["categories"],
    #                                       self.candidate_set, len(self.query["services"]), 1, 1, 1)[0]
    #    optimized_recommendation = exp.optimizedGreedy(self.g, self.query["categories"],
    #                                                   self.candidate_set, len(self.query["services"]), 1, 1, 1)[0]
    #    self.assertEqual(normal_recommendation, optimized_recommendation)

    # def test_performance(self):
    #    start_time = time.time()
    #    exp.Greedy(self.g, self.query["categories"], self.candidate_set, len(self.query["services"]), 1, 1, 1)[0]
    #    normal_time = time.time() - start_time
    #    opt_start_time = time.time()
    #    exp.optimizedGreedy(self.g, self.query["categories"], self.candidate_set, len(self.query["services"]), 1, 1, 1)[0]
    #    optimized_time = time.time() - opt_start_time
    #    print("---- %s normal time -----" % normal_time)
    #    print("---- %s optimized time -----" % optimized_time)
    #    self.assertTrue(normal_time > optimized_time)


if __name__ == '__main__':
    unittest.main()
