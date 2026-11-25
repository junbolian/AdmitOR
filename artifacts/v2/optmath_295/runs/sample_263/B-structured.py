# IR: {"sets":{"I":"range(num_origins)","J":"range(num_destinations)"},"params":{"num_origins":"params['num_origins']; frozen integer","num_destinations":"params['num_destinations']; frozen integer","supply[i]":"params['supply'][i]","demand[j]":"params['demand'][j]","cost[i,j]":"params['cost'][i][j]","capacity[i,j]":"params['capacity'][i][j]"},"variables":{"shipment[i,j]":"continuous nonnegative"},"constraints":["supply_balance[i]: sum(shipment[i,j] for j in J) == supply[i]","demand_balance[j]: sum(shipment[i,j] for i in I) == demand[j]","route_capacity[i,j]: shipment[i,j] <= capacity[i,j]"],"objective":"minimize sum(cost[i,j] * shipment[i,j] for i in I for j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_origins = params["num_origins"]
    num_destinations = params["num_destinations"]
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.origins = pyo.Set(initialize=range(num_origins), ordered=True)
    model.destinations = pyo.Set(
        initialize=range(num_destinations), ordered=True
    )

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda mdl, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: capacity[i][j],
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_balance_rule(mdl, i):
        return sum(
            mdl.shipment[i, j] for j in mdl.destinations
        ) == mdl.supply[i]

    def demand_balance_rule(mdl, j):
        return sum(
            mdl.shipment[i, j] for i in mdl.origins
        ) == mdl.demand[j]

    def route_capacity_rule(mdl, i, j):
        return mdl.shipment[i, j] <= mdl.capacity[i, j]

    model.supply_balance = pyo.Constraint(
        model.origins, rule=supply_balance_rule
    )
    model.demand_balance = pyo.Constraint(
        model.destinations, rule=demand_balance_rule
    )
    model.route_capacity = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=route_capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}