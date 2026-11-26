import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cap = params["capacity_matrix"]
    n = 9
    source = 0
    sink = 8

    nodes = list(range(n))
    edges = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()
    model.nodes = pyo.Set(initialize=nodes)
    model.edges = pyo.Set(initialize=edges, dimen=2)

    model.flow = pyo.Var(model.edges, domain=pyo.NonNegativeReals, bounds=(0, None))

    def edge_ub(mdl, i, j):
        return mdl.flow[i, j] <= cap[i][j]
    model.edge_cap = pyo.Constraint(model.edges, rule=edge_ub)

    def flow_balance(mdl, k):
        inflow = sum(mdl.flow[i, k] for i in nodes if i != k)
        outflow = sum(mdl.flow[k, j] for j in nodes if j != k)
        if k == source:
            return outflow - inflow >= 0
        elif k == sink:
            return inflow - outflow >= 0
        else:
            return inflow - outflow == 0
    model.balance = pyo.Constraint(model.nodes, rule=flow_balance)

    def obj_rule(mdl):
        return sum(mdl.flow[source, j] for j in nodes if j != source)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}