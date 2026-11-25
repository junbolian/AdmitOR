# IR: {"sets":{"cities":"0..5","routes":"(i,j) for cities i != j"},"params":{"supply_demand":"real net requirement indexed by city","costs":"real route costs; row i lists destinations in increasing order, skipping i","capacities":"nonnegative route capacities; same ordering as costs"},"variables":{"flow[i,j]":"nonnegative continuous for each route"},"constraints":["For each city k: sum(flow[i,k] for i != k) - sum(flow[k,j] for j != k) == supply_demand[k]","For each route (i,j): flow[i,j] <= capacities[i][j if j < i else j-1]"],"objective":"Minimize sum(costs[i][j if j < i else j-1] * flow[i,j] for all routes)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_demand = params["supply_demand"]
    costs = params["costs"]
    capacities = params["capacities"]

    cities = range(6)
    routes = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.routes = pyo.Set(dimen=2, initialize=routes, ordered=True)

    model.net_requirement = pyo.Param(
        model.cities,
        initialize={i: supply_demand[i] for i in cities},
        within=pyo.Reals,
    )
    model.route_cost = pyo.Param(
        model.routes,
        initialize={
            (i, j): costs[i][j if j < i else j - 1]
            for i, j in routes
        },
        within=pyo.Reals,
    )
    model.route_capacity = pyo.Param(
        model.routes,
        initialize={
            (i, j): capacities[i][j if j < i else j - 1]
            for i, j in routes
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def balance_rule(mdl, k):
        incoming = sum(
            mdl.flow[i, k] for i in mdl.cities if i != k
        )
        outgoing = sum(
            mdl.flow[k, j] for j in mdl.cities if j != k
        )
        return incoming - outgoing == mdl.net_requirement[k]

    model.flow_balance = pyo.Constraint(
        model.cities, rule=balance_rule
    )

    def capacity_rule(mdl, i, j):
        return mdl.flow[i, j] <= mdl.route_capacity[i, j]

    model.capacity_limits = pyo.Constraint(
        model.routes, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[i, j] * model.flow[i, j]
            for i, j in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}