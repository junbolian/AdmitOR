# IR: {"sets":{"I":"0..9","J":"0..7"},"params":{"supply":"supply[i] from params","demand":"demand[j] from params","cost":"cost[i][j] from params","ship_limit":"ship_limit[i][j] from params"},"variables":{"ship[i,j]":"nonnegative real"},"constraints":["sum_j ship[i,j] <= supply[i] for each i","sum_i ship[i,j] == demand[j] for each j","ship[i,j] <= ship_limit[i][j] for each i,j"],"objective":"minimize sum_i sum_j cost[i][j]*ship[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    ship_limit = params["ship_limit"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 9)
    model.destinations = pyo.RangeSet(0, 7)

    model.supply_data = pyo.Param(
        model.origins, initialize=lambda mdl, i: supply[i]
    )
    model.demand_data = pyo.Param(
        model.destinations, initialize=lambda mdl, j: demand[j]
    )
    model.cost_data = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: cost[i][j],
    )
    model.limit_data = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: ship_limit[i][j],
    )

    model.ship = pyo.Var(
        model.origins, model.destinations, domain=pyo.NonNegativeReals
    )

    model.supply_constraints = pyo.Constraint(
        model.origins,
        rule=lambda mdl, i: (
            sum(mdl.ship[i, j] for j in mdl.destinations)
            <= mdl.supply_data[i]
        ),
    )
    model.demand_constraints = pyo.Constraint(
        model.destinations,
        rule=lambda mdl, j: (
            sum(mdl.ship[i, j] for i in mdl.origins)
            == mdl.demand_data[j]
        ),
    )
    model.shipping_constraints = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=lambda mdl, i, j: mdl.ship[i, j] <= mdl.limit_data[i, j],
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_data[i, j] * model.ship[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    # HiGHS may raise when no feasible solution can be loaded.
    # Objective retrievability, not solver termination enums, determines success.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}