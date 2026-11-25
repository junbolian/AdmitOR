# IR: {"sets":{"I":"0..11","J":"0..9"},"params":{"supply":"I -> available units","demand":"J -> required units","transport_cost":"I x J -> unit cost"},"variables":{"shipment[i,j]":"nonnegative continuous, i in I, j in J"},"constraints":["sum(j in J, shipment[i,j]) = supply[i] for each i in I","sum(i in I, shipment[i,j]) = demand[j] for each j in J"],"objective":"minimize sum(i in I, j in J, transport_cost[i,j] * shipment[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 11)
    model.destinations = pyo.RangeSet(0, 9)

    model.supply = pyo.Param(
        model.origins,
        initialize={i: supply[i] for i in model.origins},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize={j: demand[j] for j in model.destinations},
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): transport_cost[i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mod, i):
        return (
            sum(mod.shipment[i, j] for j in mod.destinations)
            == mod.supply[i]
        )

    def demand_rule(mod, j):
        return (
            sum(mod.shipment[i, j] for i in mod.origins)
            == mod.demand[j]
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
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}