import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_nodes = params["num_nodes"]
    num_commodities = params["num_commodities"]
    arcs = params["arcs"]
    arc_capacity = params["arc_capacity"]
    commodity_demand = params["commodity_demand"]
    commodity_source = params["commodity_source"]
    commodity_sink = params["commodity_sink"]

    model = pyo.ConcreteModel()

    model.NODES = pyo.RangeSet(0, num_nodes - 1)
    model.COMMODITIES = pyo.RangeSet(0, num_commodities - 1)
    model.ARCS = pyo.Set(initialize=[(int(a), int(b)) for a, b in arcs], dimen=2)

    cap = {}
    for idx, (a, b) in enumerate(arcs):
        cap[(int(a), int(b))] = arc_capacity[idx]

    model.arc_cap = pyo.Param(model.ARCS, initialize=cap, mutable=True)

    model.flow = pyo.Var(model.ARCS, model.COMMODITIES, domain=pyo.NonNegativeReals)
    model.util = pyo.Var(domain=pyo.NonNegativeReals)

    # Big-M upper bound for utilization (at least 1, safe)
    model.util.setub(1e6)

    # Node balance for each commodity
    def balance_rule(m, node, k):
        inflow = sum(m.flow[i, j, k] for (i, j) in m.ARCS if j == node)
        outflow = sum(m.flow[i, j, k] for (i, j) in m.ARCS if i == node)
        supply = 0.0
        if node == commodity_source[k]:
            supply = supply + commodity_demand[k]
        if node == commodity_sink[k]:
            supply = supply - commodity_demand[k]
        return inflow - outflow + supply == 0

    model.balance = pyo.Constraint(model.NODES, model.COMMODITIES, rule=balance_rule)

    # Utilization linking constraints
    def util_rule(m, i, j):
        total = sum(m.flow[i, j, k] for k in m.COMMODITIES)
        return total <= m.util * m.arc_cap[i, j]

    model.util_con = pyo.Constraint(model.ARCS, rule=util_rule)

    def obj_rule(m):
        return m.util

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}