import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_slots = params["n_slots"]
    edges = params["edges"]

    edge_list = [tuple(e) for e in edges]
    edge_index = list(range(len(edge_list)))

    # For each slot, which edge indices are incident to it
    incident = {i: [] for i in range(n_slots)}
    for idx, (u, v) in enumerate(edge_list):
        incident[u].append(idx)
        incident[v].append(idx)

    model = pyo.ConcreteModel()

    model.slots = pyo.Set(initialize=list(range(n_slots)))
    model.edge_ids = pyo.Set(initialize=edge_index)

    model.x = pyo.Var(model.edge_ids, domain=pyo.Binary)

    # Objective: maximize number of selected edges
    def obj_rule(m):
        return sum(m.x[k] for k in m.edge_ids)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Constraint: each slot incident to at most one selected edge
    def slot_rule(m, i):
        return sum(m.x[k] for k in incident[i]) <= 1

    model.slot_con = pyo.Constraint(model.slots, rule=slot_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}