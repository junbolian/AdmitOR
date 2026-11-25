# IR: {"sets":{"cities":"0..8","routes":"(i,j) in cities x cities where i != j"},"params":{"net_supply":"params['net_supply'][i], real, positive=supply and negative=demand","cost":"params['cost'][i][j], real","capacity":"params['capacity'][i][j], nonnegative real"},"variables":{"flow[i,j]":"nonnegative continuous for every route"},"constraints":["For every city i: sum_j flow[i,j] - sum_j flow[j,i] = net_supply[i], excluding j=i.","For every route (i,j): flow[i,j] <= capacity[i,j]."],"objective":"Minimize sum_(i,j) cost[i,j] * flow[i,j]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    net_supply = params["net_supply"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.cities = pyo.RangeSet(0, 8)
    model.routes = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(9)
            for j in range(9)
            if i != j
        ],
    )

    model.net_supply = pyo.Param(
        model.cities,
        initialize={i: net_supply[i] for i in range(9)},
        within=pyo.Reals,
    )
    model.cost = pyo.Param(
        model.routes,
        initialize={(i, j): cost[i][j] for i, j in model.routes},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.routes,
        initialize={(i, j): capacity[i][j] for i, j in model.routes},
        within=pyo.NonNegativeReals,
    )

    model.flow = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def balance_rule(block, i):
        outgoing = sum(
            block.flow[i, j] for j in block.cities if j != i
        )
        incoming = sum(
            block.flow[j, i] for j in block.cities if j != i
        )
        return outgoing - incoming == block.net_supply[i]

    model.flow_balance = pyo.Constraint(
        model.cities, rule=balance_rule
    )

    def capacity_rule(block, i, j):
        return block.flow[i, j] <= block.capacity[i, j]

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
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}