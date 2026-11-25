# IR: {"sets":{"origins":"0..10","destinations":"0..9"},"params":{"supply":"supply[i] from params['supply']","demand":"demand[j] from params['demand']","cost":"cost[i][j] from params['cost']"},"variables":{"shipment[i,j]":"continuous, nonnegative"},"constraints":["sum_j shipment[i,j] == supply[i] for each origin i","sum_i shipment[i,j] == demand[j] for each destination j"],"objective":"minimize sum_i sum_j cost[i][j] * shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 10)
    model.destinations = pyo.RangeSet(0, 9)

    model.supply = pyo.Param(
        model.origins,
        initialize={i: supply[i] for i in model.origins},
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize={j: demand[j] for j in model.destinations},
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): cost[i][j]
            for i in model.origins
            for j in model.destinations
        },
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.destinations)
            == instance.supply[i]
        )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.origins)
            == instance.demand[j]
        )

    model.supply_balance = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.destinations, rule=demand_rule)

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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}