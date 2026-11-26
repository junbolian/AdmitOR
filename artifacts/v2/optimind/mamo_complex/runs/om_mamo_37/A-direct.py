import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = list(range(9))
    source = 0
    sink = 8

    edges = []
    capacities = {}
    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            key = f"capacity_{i}_{j}"
            if key in params:
                edges.append((i, j))
                capacities[(i, j)] = params[key]

    model = pyo.ConcreteModel()

    model.flow = pyo.Var(edges, domain=pyo.NonNegativeReals)

    def flow_rule(model, i, j):
        return model.flow[(i, j)] <= capacities[(i, j)]

    model.cap = pyo.Constraint(edges, rule=flow_rule)

    def balance_rule(model, k):
        inflow = sum(model.flow[(i, k)] for (i, j) in edges if j == k)
        outflow = sum(model.flow[(k, j)] for (i, j) in edges if i == k)
        if k == source:
            return outflow - inflow >= 0
        elif k == sink:
            return inflow - outflow >= 0
        else:
            return inflow - outflow == 0

    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    def obj_rule(model):
        return sum(model.flow[(i, j)] for (i, j) in edges if i == source) - \
               sum(model.flow[(i, j)] for (i, j) in edges if j == source)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}