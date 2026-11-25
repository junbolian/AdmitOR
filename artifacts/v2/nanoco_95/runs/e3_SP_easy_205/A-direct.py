import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_costs = params["arc_costs"]
    arc_capacities = params["arc_capacities"]
    source_supply = params["source_supply"]
    sink_supply = params["sink_supply"]
    intermediate_node_supply = params["intermediate_node_supply"]

    arcs = [
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2), (1, 5),
        (2, 3), (2, 6),
        (3, 4), (3, 7),
        (4, 5),
        (5, 6), (5, 7),
        (6, 7), (6, 8),
        (7, 8),
    ]
    nodes = list(range(9))

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.NODES = pyo.Set(initialize=nodes)

    model.cost = pyo.Param(model.ARCS, initialize=dict(zip(arcs, arc_costs)))
    model.cap = pyo.Param(model.ARCS, initialize=dict(zip(arcs, arc_capacities)))

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, i, j):
        return mdl.flow[i, j] <= mdl.cap[i, j]

    model.cap_con = pyo.Constraint(model.ARCS, rule=cap_rule)

    def balance_rule(mdl, n):
        out_flow = sum(mdl.flow[i, j] for (i, j) in arcs if i == n)
        in_flow = sum(mdl.flow[i, j] for (i, j) in arcs if j == n)
        if n == 0:
            return out_flow - in_flow == source_supply
        elif n == 8:
            return out_flow - in_flow == sink_supply
        else:
            return out_flow - in_flow == intermediate_node_supply

    model.balance_con = pyo.Constraint(model.NODES, rule=balance_rule)

    def obj_rule(mdl):
        return sum(mdl.cost[i, j] * mdl.flow[i, j] for (i, j) in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}