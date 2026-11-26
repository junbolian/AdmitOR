import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = int(params["num_cities"])
    cities = list(range(num_cities))

    cap = {}
    for i in cities:
        for j in cities:
            if i != j:
                cap[(i, j)] = params.get(f"capacity_{i}_{j}", 0)

    arcs = [(i, j) for (i, j) in cap.keys() if cap[(i, j)] > 0]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.flow = pyo.Var(model.arcs, bounds=lambda m, i, j: (0, cap[(i, j)]))

    source = 0
    sink = num_cities - 1

    def flow_balance_rule(m, k):
        out_flow = sum(m.flow[k, j] for (i, j) in arcs if i == k)
        in_flow = sum(m.flow[i, k] for (i, j) in arcs if j == k)
        if k == source:
            return out_flow - in_flow >= 0
        elif k == sink:
            return in_flow - out_flow >= 0
        else:
            return out_flow - in_flow == 0

    model.flow_balance = pyo.Constraint(cities, rule=flow_balance_rule)

    model.obj = pyo.Objective(
        expr=sum(model.flow[source, j] for (i, j) in arcs if i == source)
        - sum(model.flow[i, source] for (i, j) in arcs if j == source),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}