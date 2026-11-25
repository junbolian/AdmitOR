import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = int(params["num_nodes"])
    num_arcs = int(params["num_arcs"])

    arc_list = [
        (0, 1), (0, 2), (0, 3), (0, 5),
        (1, 0), (1, 2),
        (2, 0), (2, 1), (2, 3), (2, 4),
        (3, 2), (3, 4), (3, 5),
        (4, 0), (4, 3), (4, 5),
        (5, 0), (5, 4),
    ]

    arc_min_flow = params["arc_min_flow"]
    arc_max_flow = params["arc_max_flow"]
    arc_unit_cost = params["arc_unit_cost"]

    def _get(seq, k):
        return seq[k]

    min_val = {}
    max_val = {}
    cost_val = {}
    for k, (i, j) in enumerate(arc_list):
        min_val[k] = _get(arc_min_flow, k)
        max_val[k] = _get(arc_max_flow, k)
        cost_val[k] = _get(arc_unit_cost, k)

    model = pyo.ConcreteModel()
    model.ARCS = pyo.RangeSet(0, num_arcs - 1)
    model.NODES = pyo.RangeSet(0, num_nodes - 1)

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def _bounds(mdl, k):
        return (min_val[k], mdl.flow[k], max_val[k])

    model.flow_bounds = pyo.Constraint(model.ARCS, rule=_bounds)

    def _balance(mdl, n):
        inflow = sum(mdl.flow[k] for k, (i, j) in enumerate(arc_list) if j == n)
        outflow = sum(mdl.flow[k] for k, (i, j) in enumerate(arc_list) if i == n)
        return inflow == outflow

    model.flow_balance = pyo.Constraint(model.NODES, rule=_balance)

    model.energy_cost = pyo.Objective(
        expr=sum(cost_val[k] * model.flow[k] for k in model.ARCS),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.energy_cost))
    return {"objective": obj_val, "status": "optimal"}