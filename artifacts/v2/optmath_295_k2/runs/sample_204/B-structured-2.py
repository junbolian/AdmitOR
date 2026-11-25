# IR: {"sets":{"cities":[0,1,2,3,4,5],"routes":"{(i,j): i,j in cities, i != j}"},"params":{"supply":"params['supply'][i], real","cost":"params['cost'][i][j], real, routes only","capacity":"params['capacity'][i][j], nonnegative real, routes only"},"variables":{"flow[i,j]":"nonnegative continuous, (i,j) in routes"},"constraints":["For each city i: sum(flow[i,j] for j != i) - sum(flow[j,i] for j != i) == supply[i]","For each route (i,j): flow[i,j] <= capacity[i,j]"],"objective":"Minimize sum(cost[i,j] * flow[i,j] for (i,j) in routes)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cities = pyo.RangeSet(0, 5)
    model.routes = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.cities
            for j in model.cities
            if i != j
        ],
    )

    model.supply = pyo.Param(
        model.cities,
        initialize={i: params["supply"][i] for i in model.cities},
        within=pyo.Reals,
    )
    model.cost = pyo.Param(
        model.routes,
        initialize={
            (i, j): params["cost"][i][j]
            for i, j in model.routes
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.routes,
        initialize={
            (i, j): params["capacity"][i][j]
            for i, j in model.routes
        },
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def balance_rule(instance, i):
        outgoing = sum(
            instance.flow[i, j] for j in instance.cities if j != i
        )
        incoming = sum(
            instance.flow[j, i] for j in instance.cities if j != i
        )
        return outgoing - incoming == instance.supply[i]

    model.flow_balance = pyo.Constraint(
        model.cities, rule=balance_rule
    )

    def capacity_rule(instance, i, j):
        return instance.flow[i, j] <= instance.capacity[i, j]

    model.route_capacity = pyo.Constraint(
        model.routes, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.flow[i, j]
            for i, j in model.routes
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