# IR: {"sets":{"origins":"0..10","destinations":"0..10"},"params":{"supply":"supply[i]","demand":"demand[j]","transport_cost":"transport_cost[i][j]"},"variables":{"allocation[i,j]":"nonnegative continuous"},"constraints":["For each origin i: sum_j allocation[i,j] = supply[i]","For each destination j: sum_i allocation[i,j] = demand[j]"],"objective":"Minimize sum_i sum_j transport_cost[i][j] * allocation[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 10)
    model.destinations = pyo.RangeSet(0, 10)

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda mdl, i: supply[i],
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda mdl, j: demand[j],
    )
    model.transport_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: transport_cost[i][j],
    )

    model.allocation = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, i):
        return sum(
            mdl.allocation[i, j] for j in mdl.destinations
        ) == mdl.supply[i]

    def demand_rule(mdl, j):
        return sum(
            mdl.allocation[i, j] for i in mdl.origins
        ) == mdl.demand[j]

    model.supply_balance = pyo.Constraint(
        model.origins, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.destinations, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.allocation[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when no feasible solution can be loaded.
        # Other runtime errors are unexpected and must propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}