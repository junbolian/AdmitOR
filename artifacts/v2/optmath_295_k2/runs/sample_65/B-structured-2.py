# IR: {"sets":{"F":"range(params['num_facilities'])","S":"range(params['num_stores'])"},"params":{"fixed_cost":"fixed_cost[i], i in F","shipping_cost_row0":"shipping_cost_row0[i], i in F; applied to every store because no other shipping costs are supplied","demand":"demand[j], j in S","capacity":"capacity[i], i in F","num_facilities":"number of facilities","num_stores":"number of stores"},"variables":{"opened[i]":"Binary, i in F","shipment[i,j]":"NonNegativeReals, (i,j) in F x S"},"constraints":["sum(shipment[i,j] for i in F) == demand[j], j in S","sum(shipment[i,j] for j in S) <= capacity[i]*opened[i], i in F"],"objective":"minimize sum(fixed_cost[i]*opened[i] for i in F) + sum(shipping_cost_row0[i]*shipment[i,j] for i in F for j in S)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Assumption: each facility's supplied store-0 shipping rate applies
    # to every store; store-specific rates for other stores are unavailable.
    num_facilities = params["num_facilities"]
    num_stores = params["num_stores"]
    fixed_cost = params["fixed_cost"]
    shipping_cost_row0 = params["shipping_cost_row0"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.facilities = pyo.Set(
        initialize=range(num_facilities), ordered=True
    )
    model.stores = pyo.Set(
        initialize=range(num_stores), ordered=True
    )

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize={i: fixed_cost[i] for i in range(num_facilities)},
        within=pyo.Reals,
    )
    model.shipping_cost = pyo.Param(
        model.facilities,
        initialize={i: shipping_cost_row0[i] for i in range(num_facilities)},
        within=pyo.Reals,
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize={j: demand[j] for j in range(num_stores)},
        within=pyo.NonNegativeReals,
    )
    model.facility_capacity = pyo.Param(
        model.facilities,
        initialize={i: capacity[i] for i in range(num_facilities)},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.facilities, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, j):
        return (
            pyo.quicksum(
                instance.shipment[i, j] for i in instance.facilities
            )
            == instance.store_demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(instance, i):
        return (
            pyo.quicksum(
                instance.shipment[i, j] for j in instance.stores
            )
            <= instance.facility_capacity[i] * instance.opened[i]
        )

    model.capacity_limit = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            pyo.quicksum(
                model.fixed_cost[i] * model.opened[i]
                for i in model.facilities
            )
            + pyo.quicksum(
                model.shipping_cost[i] * model.shipment[i, j]
                for i in model.facilities
                for j in model.stores
            )
        ),
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Propagate unrelated runtime errors.
        if "A feasible solution was not found" not in str(exc):
            raise
        failure_reason = "no_feasible_solution"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}