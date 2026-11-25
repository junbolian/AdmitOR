# IR: {"sets":{"cities":"0..6","arcs":"(i,j) in cities x cities with i != j"},"params":{"b[i]":"params['net_supply'][i]","cost[i,j]":"params['cost_i_j']","capacity[i,j]":"params['cap_i_j']"},"variables":{"flow[i,j]":"nonnegative continuous"},"constraints":["For each city i: sum_j flow[i,j] - sum_j flow[j,i] = b[i], excluding j=i.","For each arc (i,j): flow[i,j] <= capacity[i,j]."],"objective":"Minimize sum_(i,j in arcs) cost[i,j] * flow[i,j]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = list(range(7))
    arcs = [(i, j) for i in cities for j in cities if i != j]

    net_supply = params["net_supply"]
    costs = {(i, j): params[f"cost_{i}_{j}"] for i, j in arcs}
    capacities = {(i, j): params[f"cap_{i}_{j}"] for i, j in arcs}

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)

    model.net_supply = pyo.Param(
        model.cities,
        initialize={i: net_supply[i] for i in cities},
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.capacity = pyo.Param(
        model.arcs, initialize=capacities, within=pyo.Reals
    )
    model.flow = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def balance_rule(instance, i):
        outgoing = sum(
            instance.flow[i, j] for j in instance.cities if j != i
        )
        incoming = sum(
            instance.flow[j, i] for j in instance.cities if j != i
        )
        return outgoing - incoming == instance.net_supply[i]

    model.flow_balance = pyo.Constraint(model.cities, rule=balance_rule)

    def capacity_rule(instance, i, j):
        return instance.flow[i, j] <= instance.capacity[i, j]

    model.capacity_limit = pyo.Constraint(model.arcs, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.flow[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}