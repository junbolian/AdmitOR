# IR: {"sets":{"cities":"{0,1,2,3,4,5}","arcs":"{(i,j): i,j in cities, i != j}, ordered lexicographically"},"params":{"supply_demand":"real vector indexed by cities","cost_matrix":"real vector indexed by ordered arcs","capacity_matrix":"nonnegative real vector indexed by ordered arcs"},"variables":{"flow[i,j]":"nonnegative continuous, for each (i,j) in arcs"},"constraints":["For each city i: sum(flow[i,j] for j != i) - sum(flow[j,i] for j != i) = supply_demand[i]","For each arc (i,j): flow[i,j] <= capacity_matrix[i,j]"],"objective":"Minimize sum(cost_matrix[i,j] * flow[i,j] for (i,j) in arcs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_demand = params["supply_demand"]
    cost_matrix = params["cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    cities = list(range(6))
    arcs = [(i, j) for i in cities for j in cities if i != j]

    if (
        len(supply_demand) != len(cities)
        or len(cost_matrix) != len(arcs)
        or len(capacity_matrix) != len(arcs)
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)

    model.net_supply = pyo.Param(
        model.cities,
        initialize={i: supply_demand[i] for i in cities},
        within=pyo.Reals,
    )
    model.unit_cost = pyo.Param(
        model.arcs,
        initialize={arc: cost_matrix[k] for k, arc in enumerate(arcs)},
        within=pyo.Reals,
    )
    model.route_capacity = pyo.Param(
        model.arcs,
        initialize={arc: capacity_matrix[k] for k, arc in enumerate(arcs)},
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(current_model, i):
        outbound = sum(
            current_model.flow[i, j] for j in current_model.cities if j != i
        )
        inbound = sum(
            current_model.flow[j, i] for j in current_model.cities if j != i
        )
        return outbound - inbound == current_model.net_supply[i]

    model.flow_balance = pyo.Constraint(model.cities, rule=balance_rule)

    def capacity_rule(current_model, i, j):
        return (
            current_model.flow[i, j]
            <= current_model.route_capacity[i, j]
        )

    model.capacity_limits = pyo.Constraint(model.arcs, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.flow[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}