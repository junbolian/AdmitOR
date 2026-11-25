# IR: {"sets":{"I":"0..6","J":"0..6"},"params":{"supply":"params['supply'][i], i in I","demand":"params['demand'][j], j in J","transport_cost":"params['transport_cost'][i][j], (i,j) in I x J"},"variables":{"shipment[i,j]":"NonNegativeReals, (i,j) in I x J"},"constraints":["sum(shipment[i,j] for j in J) == supply[i], for each i in I","sum(shipment[i,j] for i in I) == demand[j], for each j in J"],"objective":"minimize sum(transport_cost[i,j] * shipment[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 6)
    model.J = pyo.RangeSet(0, 6)

    model.supply = pyo.Param(
        model.I,
        initialize=lambda mdl, i: params["supply"][i],
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.J,
        initialize=lambda mdl, j: params["demand"][j],
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: params["transport_cost"][i][j],
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.I, model.J, domain=pyo.NonNegativeReals
    )

    model.supply_balance = pyo.Constraint(
        model.I,
        rule=lambda mdl, i: (
            sum(mdl.shipment[i, j] for j in mdl.J) == mdl.supply[i]
        ),
    )
    model.demand_balance = pyo.Constraint(
        model.J,
        rule=lambda mdl, j: (
            sum(mdl.shipment[i, j] for i in mdl.I) == mdl.demand[j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.shipment[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}