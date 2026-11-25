import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    capacity = params["capacity"]
    unit_cost = params["unit_cost"]
    coords_x = params["coords_x"]
    coords_y = params["coords_y"]

    num_nodes = 7
    nodes = list(range(num_nodes))

    # Directed arcs: warehouses 0,1,2 to plants 3,4,5,6
    arcs = [
        (0, 3), (0, 4), (0, 5), (0, 6),
        (1, 3), (1, 4), (1, 5), (1, 6),
        (2, 3), (2, 4), (2, 5), (2, 6),
    ]

    # Map each arc to its index in the params lists (order as given)
    arc_index = {a: k for k, a in enumerate(arcs)}

    model = pyo.ConcreteModel()

    model.ARC = pyo.Set(initialize=arcs, dimen=2)
    model.NODE = pyo.Set(initialize=nodes)

    model.flow = pyo.Var(model.ARC, domain=pyo.NonNegativeReals)

    def capacity_rule(mdl, i, j):
        return mdl.flow[i, j] <= capacity[arc_index[(i, j)]]

    model.capacity_con = pyo.Constraint(model.ARC, rule=capacity_rule)

    def balance_rule(mdl, n):
        outflow = sum(mdl.flow[i, j] for (i, j) in arcs if i == n)
        inflow = sum(mdl.flow[i, j] for (i, j) in arcs if j == n)
        return outflow - inflow == supply[n]

    model.balance_con = pyo.Constraint(model.NODE, rule=balance_rule)

    def obj_rule(mdl):
        return sum(unit_cost[arc_index[(i, j)]] * mdl.flow[i, j] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}