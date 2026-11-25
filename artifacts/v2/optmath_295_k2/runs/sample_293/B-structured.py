# IR: {"sets":{"origins":"0..11","destinations":"0..9"},"params":{"supply":"supply[i] from params['supply']","demand":"demand[j] from params['demand']","transport_cost":"transport_cost[i,j] from params['transport_cost']"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["For each origin i: sum_j shipment[i,j] == supply[i]","For each destination j: sum_i shipment[i,j] == demand[j]"],"objective":"Minimize sum_i sum_j transport_cost[i,j] * shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 11)
    model.destinations = pyo.RangeSet(0, 9)

    model.supply = pyo.Param(
        model.origins,
        initialize={i: params["supply"][i] for i in model.origins},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize={j: params["demand"][j] for j in model.destinations},
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): params["transport_cost"][i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.origins, model.destinations, domain=pyo.NonNegativeReals
    )

    def supply_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.destinations)
            == instance.supply[i]
        )

    model.supply_balance = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.origins)
            == instance.demand[j]
        )

    model.demand_balance = pyo.Constraint(model.destinations, rule=demand_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
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