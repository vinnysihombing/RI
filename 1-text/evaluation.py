#! /usr/bin/env python3
# -*- coding: utf-8 -*-

import query
import numpy as np
import itertools as it
import TextRepresenter

class IRList():
    """ Contains a query and the scores found for this query """
    def __init__(self, query, scores):
        """ Create new IRList
        :param query: The Query object
        :param scores: a list of tuples [(docId, score)]"""
        self.query = query
        self.scores = scores # List [(docId, score)]

    def getQuery(self):
        return self.query

    def getScores(self):
        return self.scores


class EvalMeasure:
    """ The abstract class for measure methods """
    def __init__(self, irlist):
        self.irlist = irlist

    def getRelevantResults(self):
        """ Return the relevant results for the query in the
        IRList object"""
        # The relevant results of the query are the ones that have
        # a score higher than mean:
        mean = np.mean([score for (docId, score) in self.irlist.getScores()])
        relevantResults = [docId for (docId, score) in self.irlist.getScores()
                          if score > mean]
        return relevantResults

    def eval(self):
        raise NotImplementedError("Abstract method")


class PrecisionRecallMeasure(EvalMeasure):

    def __init__(self, irlist):
        super().__init__(irlist)

    def eval(self, verbose=False, nbLevel=11):
        """ Compute the recall and precision for an IRList
        :param verbose: bool, whether or not to display messages
        :param nbLevel: int, optional (default is 11). The number of 
        (precision, recall) values to compute
        :return: A sorted list of (recall, precision)"""
        rec_prec = {}
        # Truely relevant results for the query:
        trueRels = list(self.irlist.getQuery().getRelevants().keys())
        # Results we found for the query:
        results = super().getRelevantResults()

        if verbose:
            print("This query has %d relevant results" 
                % len(trueRels))
            # print("Scores for this query:", self.irlist.getScores())
            print("   i |found| precision | recall")
        for i in range(1, len(results)):
            # Number of results we found that are really relevant:
            relevantFound = len(np.intersect1d(results[:i], trueRels))
            prec = relevantFound/i
            rec = relevantFound/len(trueRels)
            if verbose:
                print("%5d|%4d | %5f  |%5f" % (i, relevantFound, prec, rec))

            if rec not in rec_prec.keys():
                rec_prec[rec] = prec
            elif prec > rec_prec[rec]:
                rec_prec[rec] = prec

        results = []
        keys = list(rec_prec.keys())
        for recall in np.linspace(0, 1, nbLevel):
            # Find the closest point to recall
            idx = np.argmin(list(map(lambda n:np.abs(n-recall), keys)))
            # print("Closest recall to %f is %f" % (recall, keys[idx]))
            # print("idx=%d, keys[idx]=%f" %(idx, keys[idx]))
            results.append((keys[idx], rec_prec[keys[idx]]))

        # print(results)
        return results


class AveragePrecision(EvalMeasure):

    def __init__(self, irlist):
        super().__init__(irlist)

    def eval(self, verbose=False, step=1):
        """ Compute the performance of a model.
        :param step: int, optional (default is 1). 
            The step used to iterate over all results.
            (Lets the evaluation skip some results to evaluate faster)
        :return: The average precision at different ranks"""
        s = 0 # The sum of precisions. 
        # Truely relevant results for the query:
        trueRels = list(self.irlist.getQuery().getRelevants().keys())
        # Results we found for the query:
        results = super().getRelevantResults()

        if verbose:
            print("This query has %d relevant results" 
                % len(trueRels))
            # print("Scores for this query:", self.irlist.getScores())
            print("   i |found| precision")
        for i in range(1, len(results), step):
            # Number of results we found that are really relevant:
            relevantFound = len(np.intersect1d(results[:i], trueRels))
            # print("Doc at rank %d is %s." % (i, results[i-1]))
            # print("doc in trueRels:", results[i-1] in trueRels)
            if int(results[i-1]) in trueRels:
                # if verbose:
                    # print("Document at rank %d is relevant" % i)
                prec = relevantFound/i
            else:
                prec = 0
            if verbose:
                print("%5d|%4d | %5f" % (i, relevantFound, prec))
            s += prec

        return s/len(trueRels)

class EvalIRModel():
    def __init__(self, queries, irmodels, measures, stemmer=TextRepresenter.PorterStemmer()):
        """
        :param queries: List of Query objects
        :param irmodels: dictionary of {name:IRmodel object}
        :param evals: dictionary of {name:EvalMeasure class}"""
        self.queries = queries
        self.irmodels = irmodels
        self.measures = measures
        self.stemmer = stemmer

    def eval(self):
        print("irmodel, measure, mean(score)")
        all_query_scores = []
            
        for irmodel_name, irmodel in self.irmodels.items():
            print("IRModel:", irmodel_name)
            for q in self.queries:
                print("Retrieve scores for query #" + q.getID())
                q_scores = irmodel.getScores(self.stemmer.
                            getTextRepresentation(q.getText()))
                all_query_scores.append(list(q_scores.items()))
            for measure_name, measure_class in self.measures.items():
                print("Measure:", measure_name)
                eval_scores = []
                for q_scores in all_query_scores:
                    measure = measure_class(IRList(q, q_scores))
                    eval_scores.append(measure.eval())
                print(irmodel_name, measure_name, eval_scores)

