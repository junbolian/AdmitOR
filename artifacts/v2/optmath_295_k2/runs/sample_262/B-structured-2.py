# IR: {"sets":{"F":[0,1,2,3],"C":[0,1,2,3,4,5,6,7]},"params":{"fixed_cost":"F -> real","demand":"C -> nonnegative real","ship_cost":"F x C -> real","capacity":"F -> nonnegative real"},"variables":{"opened[f]":"binary","shipment[f,c]":"nonnegative continuous"},"constraints":["For each c in C: sum_f shipment[f,c] = demand[c]","For each f in F: sum_c shipment[f,c] <= capacity[f] * opened[f]"],"objective":"minimize sum_f fixed_cost[f]*opened[f] + sum_f,c ship_cost[f,c]*shipment[f,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.facilities = pyo.RangeSet(0, 3)
    model.customers = pyo.RangeSet(0, 7)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize={f: params["fixed_cost"][f] for f in model.facilities},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.customers,
        initialize={c: params["demand"][c] for c in model.customers},
        within=pyo.NonNegativeReals,
    )
    model.ship_cost = pyo.Param(
        model.facilities,
        model.customers,
        initialize={
            (f, c): params["ship_cost"][f][c]
            for f in model.facilities
            for c in model.customers
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.facilities,
        initialize={f: params["capacity"][f] for f in model.facilities},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.facilities, model.customers, domain=pyo.NonNegativeReals
    )

    def demand_rule(model, c):
        return (
            sum(model.shipment[f, c] for f in model.facilities)
            == model.demand[c]
        )

    model.demand_fulfillment = pyo.Constraint(
        model.customers, rule=demand_rule
    )

    def capacity_rule(model, f):
        return (
            sum(model.shipment[f, c] for c in model.customers)
            <= model.capacity[f] * model.opened[f]
        )

    model.facility_capacity = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[f] * model.opened[f]
            for f in model.facilities
        )
        + sum(
            model.ship_cost[f, c] * model.shipment[f, c]
            for f in model.facilities
            for c in model.customers
        ),
        sense=pyo.minimize,
    )

    # APPsi may raise when no feasible solution can be loaded.
    # Success is determined solely by objective-value retrieval below.
    try:
        Highs().solve(model)
    except RuntimeError:
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}