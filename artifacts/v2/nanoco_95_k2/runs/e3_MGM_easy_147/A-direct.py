import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = params["edges"]
    num_nodes = params["num_nodes"]

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, num_nodes - 1)
    model.edges = pyo.Set(initialize=[tuple(e) for e in edges], dimen=2)

    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(model.x[e] for e in model.edges),
        sense=pyo.maximize,
    )

    model.incident = pyo.ConstraintList()
    for i in model.nodes:
        incident_edges = [e for e in model.edges if (e[0] == i or e[1] == i)]
        model.incident.add(sum(model.x[e] for e in incident_edges) <= 1)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}