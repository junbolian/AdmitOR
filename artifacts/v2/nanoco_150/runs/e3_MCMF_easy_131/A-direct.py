import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacities = params["capacities"]
    unit_costs = params["unit_costs"]

    arcs = [
        (0, 1), (1, 2), (1, 7), (2, 3), (2, 6), (3, 4), (3, 8), (3, 9),
        (4, 5), (4, 8), (5, 6), (6, 7), (7, 8), (7, 9), (8, 9),
    ]
    arc_index = list(range(len(arcs)))

    cap = {k: capacities[k] for k in arc_index}
    cost = {k: unit_costs[k] for k in arc_index}

    intermediate = [1, 2, 3, 4, 5, 6, 7, 8]

    model = pyo.ConcreteModel()
    model.ARC = pyo.Set(initialize=arc_index)
    model.INTER = pyo.Set(initialize=intermediate)

    model.flow = pyo.Var(model.ARC, domain=pyo.NonNegativeReals,
                         bounds=lambda m, k: (0, cap[k]))

    outflow = {n: sum(model.flow[k] for k in arc_index if arcs[k][0] == n)
               for n in intermediate}
    inflow = {n: sum(model.flow[k] for k in arc_index if arcs[k][1] == n)
              for n in intermediate}

    model.cons_flow = pyo.Constraint(
        model.INTER, rule=lambda m, n: inflow[n] == outflow[n])

    return_expr = sum(model.flow[k] for k in arc_index if arcs[k][0] == 0)
    cost_expr = sum(cost[k] * model.flow[k] for k in arc_index)

    # Lexicographic: maximize delivered volume, then minimize cost.
    # Scale factor large enough to make volume dominate cost.
    cost_scale = sum(cap[k] for k in arc_index) * max(cost.values()) + 1

    model.obj = pyo.Objective(
        expr=cost_scale * return_expr - cost_expr,
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}