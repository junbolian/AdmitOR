import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):

    farms = [0, 1, 2]
    retails = [3, 4, 5, 6]

    arcs = [
        (0, 3), (0, 4), (0, 5), (0, 6),
        (1, 3), (1, 4), (1, 5), (1, 6),
        (2, 3), (2, 4), (2, 5), (2, 6),
    ]

    farm_supply_raw = params["farm_supply"]
    retail_demand_raw = params["retail_demand"]
    arc_capacities = params["arc_capacities"]
    arc_unit_costs = params["arc_unit_costs"]

    def to_map_sequential(raw, keys):
        if isinstance(raw, dict):
            return {k: raw[k] for k in keys}
        return {k: raw[i] for i, k in enumerate(keys)}

    def to_map_node_indexed(raw, keys):
        if isinstance(raw, dict):
            return {k: raw[k] for k in keys}
        offset = min(keys)
        try:
            return {k: raw[k - offset] for k in keys}
        except (IndexError, KeyError, TypeError):
            return {k: raw[i] for i, k in enumerate(keys)}

    capacity = {arc: arc_capacities[i] for i, arc in enumerate(arcs)}
    cost = {arc: arc_unit_costs[i] for i, arc in enumerate(arcs)}

    supply = to_map_node_indexed(farm_supply_raw, farms)
    demand = to_map_node_indexed(retail_demand_raw, retails)

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[a] * m.flow[a] for a in m.ARCS)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.capacity_con = pyo.Constraint(
        model.ARCS,
        rule=lambda m, a: m.flow[a] <= capacity[a],
    )

    model.supply_con = pyo.Constraint(
        farms,
        rule=lambda m, f: sum(m.flow[a] for a in m.ARCS if a[0] == f) == supply[f],
    )

    model.demand_con = pyo.Constraint(
        retails,
        rule=lambda m, r: sum(m.flow[a] for a in m.ARCS if a[1] == r) == demand[r],
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}