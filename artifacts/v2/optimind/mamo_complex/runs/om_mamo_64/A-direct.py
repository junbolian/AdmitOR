import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = list(range(8))
    source = 0
    dest = 7

    arcs = [(i, j) for i in cities for j in cities if i != j]

    def cap(i, j):
        return params["capacity_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()

    model.ARC = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.ARC, domain=pyo.NonNegativeReals)

    def flow_bound_rule(mdl, i, j):
        return mdl.flow[i, j] <= cap(i, j)

    model.flow_bound = pyo.Constraint(model.ARC, rule=flow_bound_rule)

    def balance_rule(mdl, k):
        incoming = sum(mdl.flow[i, k] for i in cities if i != k)
        outgoing = sum(mdl.flow[k, j] for j in cities if j != k)
        if k == source:
            return outgoing - incoming >= 0
        elif k == dest:
            return incoming - outgoing >= 0
        else:
            return incoming - outgoing == 0

    model.balance = pyo.Constraint(cities, rule=balance_rule)

    def obj_rule(mdl):
        return sum(mdl.flow[source, j] for j in cities if j != source)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}