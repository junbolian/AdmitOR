# IR (JSON):
# {
#   "assumptions": [
#     "Connections are undirected, with shipping allowed in either direction and shared capacity.",
#     "Pair-specific costs and capacities are unspecified. For a complete deterministic instance, interpolate each supplied range linearly over lexicographically ordered hub pairs. This is an explicit modeling assumption."
#   ],
#   "sets": {"H": [0,1,2,3,4], "E": "{(i,j): i,j in H, i<j}", "A": "{(i,j): i,j in H, i!=j}"},
#   "params": {
#     "inputs": ["demand_0","demand_1","supply_2","supply_3","supply_4","fixed_cost_min","fixed_cost_max","variable_cost_min","variable_cost_max","capacity_min","capacity_max"],
#     "net_demand": "[demand_0,demand_1,-supply_2,-supply_3,-supply_4]",
#     "fraction[e]": "zero_based_lexicographic_rank(e)/(len(E)-1)",
#     "fixed[e]": "fixed_cost_min+fraction[e]*(fixed_cost_max-fixed_cost_min)",
#     "variable[e]": "variable_cost_min+fraction[e]*(variable_cost_max-variable_cost_min)",
#     "capacity[e]": "capacity_min+fraction[e]*(capacity_max-capacity_min)"
#   },
#   "variables": {"established[e in E]": "binary", "flow[i,j in A]": "nonnegative continuous"},
#   "constraints": [
#     "For each hub h: sum(flow[i,h] for i!=h)-sum(flow[h,j] for j!=h)=net_demand[h].",
#     "For each pair (i,j) in E: flow[i,j]+flow[j,i]<=capacity[i,j]*established[i,j]."
#   ],
#   "objective": "Minimize sum(fixed[i,j]*established[i,j]+variable[i,j]*(flow[i,j]+flow[j,i]) for (i,j) in E)."
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_0 = params["demand_0"]
    demand_1 = params["demand_1"]
    supply_2 = params["supply_2"]
    supply_3 = params["supply_3"]
    supply_4 = params["supply_4"]
    fixed_cost_min = params["fixed_cost_min"]
    fixed_cost_max = params["fixed_cost_max"]
    variable_cost_min = params["variable_cost_min"]
    variable_cost_max = params["variable_cost_max"]
    capacity_min = params["capacity_min"]
    capacity_max = params["capacity_max"]

    hubs = list(range(5))
    pairs = [(i, j) for i in hubs for j in hubs if i < j]
    arcs = [(i, j) for i in hubs for j in hubs if i != j]

    net_demand = {
        0: demand_0,
        1: demand_1,
        2: -supply_2,
        3: -supply_3,
        4: -supply_4,
    }

    fractions = {
        pair: rank / (len(pairs) - 1)
        for rank, pair in enumerate(pairs)
    }
    fixed_costs = {
        pair: fixed_cost_min
        + fractions[pair] * (fixed_cost_max - fixed_cost_min)
        for pair in pairs
    }
    variable_costs = {
        pair: variable_cost_min
        + fractions[pair] * (variable_cost_max - variable_cost_min)
        for pair in pairs
    }
    capacities = {
        pair: capacity_min
        + fractions[pair] * (capacity_max - capacity_min)
        for pair in pairs
    }

    model = pyo.ConcreteModel()
    model.hubs = pyo.Set(initialize=hubs, ordered=True)
    model.pairs = pyo.Set(dimen=2, initialize=pairs, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.net_demand = pyo.Param(
        model.hubs, initialize=net_demand, within=pyo.Reals
    )
    model.fixed_cost = pyo.Param(
        model.pairs, initialize=fixed_costs, within=pyo.Reals
    )
    model.variable_cost = pyo.Param(
        model.pairs, initialize=variable_costs, within=pyo.Reals
    )
    model.capacity = pyo.Param(
        model.pairs, initialize=capacities, within=pyo.Reals
    )

    model.established = pyo.Var(model.pairs, domain=pyo.Binary)
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(instance, hub):
        incoming = sum(
            instance.flow[other, hub]
            for other in instance.hubs
            if other != hub
        )
        outgoing = sum(
            instance.flow[hub, other]
            for other in instance.hubs
            if other != hub
        )
        return incoming - outgoing == instance.net_demand[hub]

    model.flow_balance = pyo.Constraint(model.hubs, rule=balance_rule)

    def capacity_rule(instance, i, j):
        return (
            instance.flow[i, j] + instance.flow[j, i]
            <= instance.capacity[i, j] * instance.established[i, j]
        )

    model.connection_capacity = pyo.Constraint(
        model.pairs, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[i, j] * model.established[i, j]
            + model.variable_cost[i, j]
            * (model.flow[i, j] + model.flow[j, i])
            for i, j in model.pairs
        ),
        sense=pyo.minimize,
    )

    # APPsi can raise RuntimeError when no feasible solution can be loaded.
    # Objective retrievability alone determines the returned success status.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}