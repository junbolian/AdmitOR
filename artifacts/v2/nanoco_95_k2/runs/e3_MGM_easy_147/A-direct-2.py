import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = params["edges"]
    num_nodes = params["num_nodes"]

    model = pyo.ConcreteModel()
    model.E = pyo.Set(initialize=range(len(edges)))
    model.x = pyo.Var(model.E, domain=pyo.Binary)

    incidence = {n: [] for n in range(num_nodes)}
    for e_idx, (u, v) in enumerate(edges):
        incidence[u].append(e_idx)
        incidence[v].append(e_idx)

    model.node_cons = pyo.ConstraintList()
    for n in range(num_nodes):
        model.node_cons.add(sum(model.x[e] for e in incidence[n]) <= 1)

    model.obj = pyo.Objective(expr=sum(model.x[e] for e in model.E), sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}