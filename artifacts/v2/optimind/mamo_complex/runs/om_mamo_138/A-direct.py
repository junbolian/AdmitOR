import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [0, 1, 2, 3, 4, 5]
    source = 0
    sink = 5

    edge_list = []
    for i in cities:
        for j in cities:
            if i == j:
                continue
            key = f"cap_{i}_{j}"
            if key in params:
                edge_list.append((i, j))
    edge_tuples = [(i, j) for (i, j) in edge_list]

    model = pyo.ConcreteModel()
    model.EDGES = pyo.Set(initialize=edge_tuples, dimen=2)

    cap_dict = {(i, j): params[f"cap_{i}_{j}"] for (i, j) in edge_tuples}
    model.cap = pyo.Param(model.EDGES, initialize=cap_dict)

    model.x = pyo.Var(model.EDGES, domain=pyo.NonNegativeReals)
    model.total_flow = pyo.Var(domain=pyo.NonNegativeReals)

    def flow_rule(mdl, i, j):
        return mdl.x[(i, j)] <= mdl.cap[(i, j)]
    model.flow_limit = pyo.Constraint(model.EDGES, rule=flow_rule)

    def conservation_rule(mdl, k):
        out_terms = [mdl.x[(i, j)] for (i, j) in edge_tuples if i == k]
        in_terms = [mdl.x[(i, j)] for (i, j) in edge_tuples if j == k]
        net = sum(out_terms) - sum(in_terms)
        if k == source:
            return net == mdl.total_flow
        elif k == sink:
            return net == -mdl.total_flow
        else:
            return net == 0
    model.conservation = pyo.Constraint(cities, rule=conservation_rule)

    model.obj = pyo.Objective(expr=model.total_flow, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or solver failure"}

    return {"objective": obj_val, "status": "optimal"}