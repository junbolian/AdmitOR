# IR: {"sets":{"F":[0,1,2,3],"C":[0,1,2,3,4,5]},"params":{"fixed_cost":"F -> real","capacity":"F -> nonnegative real","demand":"C -> nonnegative real","shipping_cost":"F x C -> real"},"variables":{"opened[F]":"binary","shipment[F,C]":"nonnegative continuous"},"constraints":["For each j in C: sum(shipment[i,j] for i in F) == demand[j]","For each i in F: sum(shipment[i,j] for j in C) <= capacity[i]*opened[i]"],"objective":"minimize sum(fixed_cost[i]*opened[i] for i in F) + sum(shipping_cost[i,j]*shipment[i,j] for i in F for j in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using length-4/6 parameter arrays and a 4-by-6 cost matrix."""
    model = pyo.ConcreteModel()

    model.facilities = pyo.Set(initialize=range(4), ordered=True)
    model.customers = pyo.Set(initialize=range(6), ordered=True)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize=lambda mdl, i: params["fixed_cost"][i],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.facilities,
        initialize=lambda mdl, i: params["capacity"][i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.customers,
        initialize=lambda mdl, j: params["demand"][j],
        within=pyo.NonNegativeReals,
    )
    model.shipping_cost = pyo.Param(
        model.facilities,
        model.customers,
        initialize=lambda mdl, i, j: params["shipping_cost"][i][j],
        within=pyo.Reals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.facilities,
        model.customers,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.facilities)
            == mdl.demand[j]
        )

    model.demand_fulfillment = pyo.Constraint(
        model.customers, rule=demand_rule
    )

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.customers)
            <= mdl.capacity[i] * mdl.opened[i]
        )

    model.facility_capacity = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[i] * model.opened[i]
                for i in model.facilities
            )
            + sum(
                model.shipping_cost[i, j] * model.shipment[i, j]
                for i in model.facilities
                for j in model.customers
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}