# IR: {"sets":{"I":"0..13","J":"0..13"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j], or params['cost'][14*i+j] for flat row-major input"},"variables":{"shipment[i,j]":"NonNegativeReals"},"constraints":["sum(shipment[i,j] for j in J) == supply[i] for i in I","sum(shipment[i,j] for i in I) == demand[j] for j in J"],"objective":"minimize sum(cost[i,j]*shipment[i,j] for i in I for j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 13)
    model.destinations = pyo.RangeSet(0, 13)

    flat_cost = len(cost) == 14 * 14

    model.supply_amount = pyo.Param(
        model.origins,
        initialize=lambda mdl, i: supply[i],
        within=pyo.Reals,
    )
    model.demand_amount = pyo.Param(
        model.destinations,
        initialize=lambda mdl, j: demand[j],
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: (
            cost[14 * i + j] if flat_cost else cost[i][j]
        ),
        within=pyo.Reals,
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
            model.transport_cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}