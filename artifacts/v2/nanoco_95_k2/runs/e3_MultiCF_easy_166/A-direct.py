import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arc_capacities = params["arc_capacities"]
    arc_costs = params["arc_costs"]
    commodity_sources = params["commodity_sources"]
    commodity_sinks = params["commodity_sinks"]
    commodity_demands = params["commodity_demands"]

    num_nodes = 10
    arcs = [(0, 1), (1, 0), (0, 4), (4, 0), (1, 2), (2, 1), (1, 5), (5, 1),
            (2, 3), (3, 2), (2, 6), (6, 2), (3, 4), (4, 3), (3, 9), (9, 3),
            (4, 5), (5, 4), (4, 6), (6, 4), (5, 6), (6, 5), (5, 7), (7, 5),
            (6, 7), (7, 6), (7, 8), (8, 7), (8, 9), (9, 8)]
    num_arcs = len(arcs)
    num_commodities = 2

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, num_nodes - 1)
    model.arcs_idx = pyo.RangeSet(0, num_arcs - 1)
    model.commodities = pyo.RangeSet(0, num_commodities - 1)

    arc_tail = {a: arcs[a][0] for a in range(num_arcs)}
    arc_head = {a: arcs[a][1] for a in range(num_arcs)}

    model.arc_flow = pyo.Var(model.commodities, model.arcs_idx, domain=pyo.NonNegativeReals)

    def capacity_rule(model, a):
        return sum(model.arc_flow[k, a] for k in model.commodities) <= arc_capacities[a]

    model.capacity_con = pyo.Constraint(model.arcs_idx, rule=capacity_rule)

    def balance_rule(model, k, n):
        outflow = sum(model.arc_flow[k, a] for a in range(num_arcs) if arc_tail[a] == n)
        inflow = sum(model.arc_flow[k, a] for a in range(num_arcs) if arc_head[a] == n)
        if n == commodity_sources[k]:
            return outflow - inflow == commodity_demands[k]
        elif n == commodity_sinks[k]:
            return inflow - outflow == commodity_demands[k]
        else:
            return inflow - outflow == 0

    model.balance_con = pyo.Constraint(model.commodities, model.nodes, rule=balance_rule)

    def objective_rule(model):
        return sum(arc_costs[a] * model.arc_flow[k, a]
                   for k in model.commodities for a in model.arcs_idx)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}