import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 1), (1, 2), (1, 4), (1, 5), (1, 6), (1, 7),
        (2, 3), (3, 4), (4, 5), (4, 8), (4, 9),
        (5, 6), (5, 7), (6, 7), (7, 8), (7, 9), (8, 9),
    ]
    nodes = list(range(10))

    def arc_cost(a):
        return params["arc_cost_%d_%d" % (a[0], a[1])]

    capacity = params["arc_capacity"]

    supply = {i: 0 for i in nodes}
    supply[0] = params["source_supply"]
    supply[9] = params["sink_supply"]

    model = pyo.ConcreteModel()
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.NODES = pyo.Set(initialize=nodes)

    model.flow = pyo.Var(model.ARCS, within=pyo.NonNegativeReals, bounds=(0, capacity))

    def flow_rule(mdl, i):
        out_flow = sum(mdl.flow[a] for a in arcs if a[0] == i)
        in_flow = sum(mdl.flow[a] for a in arcs if a[1] == i)
        return out_flow - in_flow == supply[i]

    model.flow_con = pyo.Constraint(model.NODES, rule=flow_rule)

    model.cost = pyo.Objective(
        expr=sum(arc_cost(a) * model.flow[a] for a in arcs),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}