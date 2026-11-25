# IR: {"sets":{"origins":[0,1,2,3],"destinations":[0,1,2,3]},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]","capacity":"params['capacity'][i][j]"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum_j shipment[i,j] == supply[i] for each origin i","sum_i shipment[i,j] == demand[j] for each destination j","shipment[i,j] <= capacity[i,j] for each lane (i,j)"],"objective":"minimize sum_i sum_j cost[i,j] * shipment[i,j]"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 3)
    model.destinations = pyo.RangeSet(0, 3)

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

    def supply_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.destinations)
            == mdl.supply[i]
        )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.origins)
            == mdl.demand[j]
        )

    def capacity_rule(mdl, i, j):
        return mdl.shipment[i, j] <= mdl.capacity[i, j]

    model.supply_balance = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.destinations, rule=demand_rule)
    model.lane_limits = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=capacity_rule,
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
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}