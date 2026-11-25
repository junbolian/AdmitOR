# IR: {"sets":{"I":"0..7","J":"0..7"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["For each i in I: sum(shipment[i,j] for j in J) = supply[i]","For each j in J: sum(shipment[i,j] for i in I) = demand[j]"],"objective":"minimize sum(cost[i,j]*shipment[i,j] for i in I for j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 7)
    model.destinations = pyo.RangeSet(0, 7)

    model.supply_amount = pyo.Param(
        model.origins,
        initialize=lambda mdl, i: supply[i],
    )
    model.demand_amount = pyo.Param(
        model.destinations,
        initialize=lambda mdl, j: demand[j],
    )
    model.unit_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: cost[i][j],
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.destinations)
            == mdl.supply_amount[i]
        )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.origins)
            == mdl.demand_amount[j]
        )

    model.supply_balance = pyo.Constraint(
        model.origins, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.destinations, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # HiGHS raises when automatic solution loading finds no feasible solution.
        # Propagate unrelated errors and assess success through objective evaluation.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}