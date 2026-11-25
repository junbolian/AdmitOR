# IR: {"sets":{"F":[0,1,2,3],"C":[0,1,2,3,4,5,6,7]},"params":{"fixed_cost":"F -> Real","demand":"C -> NonNegativeReal","shipping_cost_f0":"C -> Real","shipping_cost_f1":"C -> Real","shipping_cost_f2":"C -> Real","shipping_cost_f3":"C -> Real","capacity":"F -> NonNegativeReal"},"variables":{"opened[f]":"Binary","shipped[f,c]":"NonNegativeReal"},"constraints":["forall c in C: sum(f in F, shipped[f,c]) == demand[c]","forall f in F: sum(c in C, shipped[f,c]) <= capacity[f] * opened[f]"],"objective":"minimize sum(f in F, fixed_cost[f]*opened[f]) + sum(f in F,c in C, shipping_cost_f[f][c]*shipped[f,c])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.facilities = pyo.RangeSet(0, 3)
    model.customers = pyo.RangeSet(0, 7)

    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]
    shipping_costs = (
        params["shipping_cost_f0"],
        params["shipping_cost_f1"],
        params["shipping_cost_f2"],
        params["shipping_cost_f3"],
    )

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize={f: fixed_cost[f] for f in model.facilities},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.customers,
        initialize={c: demand[c] for c in model.customers},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.facilities,
        initialize={f: capacity[f] for f in model.facilities},
        within=pyo.NonNegativeReals,
    )
    model.shipping_cost = pyo.Param(
        model.facilities,
        model.customers,
        initialize={
            (f, c): shipping_costs[f][c]
            for f in model.facilities
            for c in model.customers
        },
        within=pyo.Reals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.facilities,
        model.customers,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(instance, c):
        return (
            sum(instance.shipped[f, c] for f in instance.facilities)
            == instance.demand[c]
        )

    model.demand_fulfillment = pyo.Constraint(
        model.customers, rule=demand_rule
    )

    def capacity_rule(instance, f):
        return (
            sum(instance.shipped[f, c] for c in instance.customers)
            <= instance.capacity[f] * instance.opened[f]
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
            model.shipping_cost[f, c] * model.shipped[f, c]
            for f in model.facilities
            for c in model.customers
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        if "A feasible solution was not found" in str(error):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}