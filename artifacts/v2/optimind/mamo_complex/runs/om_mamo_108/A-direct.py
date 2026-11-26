import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    nodes = list(range(9))
    source = 0
    sink = 8

    # Directed edges with capacities read from params
    edges = []
    for i in nodes:
        for j in nodes:
            if i == j or i == sink:
                continue
            key = "cap_{}_{}".format(i, j)
            edges.append((i, j, params[key]))

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.edges = pyo.Set(initialize=[(i, j) for (i, j, c) in edges], dimen=2)

    cap = {(i, j): c for (i, j, c) in edges}
    model.edge_cap = pyo.Param(model.edges, initialize=cap, mutable=True)

    model.flow = pyo.Var(model.edges, within=pyo.NonNegativeReals)

    def inflow_rule(mdl, n):
        if n == source:
            return pyo.Constraint.Skip
        return sum(mdl.flow[i, j] for (i, j) in mdl.edges if j == n) - \
               sum(mdl.flow[i, j] for (i, j) in mdl.edges if i == n) == 0

    model.flow_balance = pyo.Constraint(model.nodes, rule=inflow_rule)

    def cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= mdl.edge_cap[i, j]

    model.capacity_limit = pyo.Constraint(model.edges, rule=cap_rule)

    def obj_rule(mdl):
        return sum(mdl.flow[i, j] for (i, j) in mdl.edges if i == source)

    model.total_flow = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_flow))
    return {'objective': obj_val, 'status': 'optimal'}