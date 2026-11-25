# IR: {"sets":{"F":[0,1,2,3],"C":[0,1,2,3,4,5,6,7,8,9]},"params":{"fixed_cost":"F-indexed nonnegative vector","demand":"C-indexed nonnegative vector","capacity":"F-indexed nonnegative vector","shipping_cost_f0":"C-indexed nonnegative vector","shipping_cost_f1":"C-indexed nonnegative vector","shipping_cost_f2":"C-indexed nonnegative vector","shipping_cost_f3":"C-indexed nonnegative vector"},"validation":["Require four fixed costs, four capacities, ten demands, and ten shipping costs per facility; return a failure status if data are incomplete."],"variables":{"opened[f]":"Binary","shipment[f,c]":"NonNegativeReals"},"constraints":["For each c: sum_f shipment[f,c] == demand[c].","For each f: sum_c shipment[f,c] <= capacity[f] * opened[f]."],"objective":"Minimize sum_f fixed_cost[f]*opened[f] + sum_f,c shipping_cost[f,c]*shipment[f,c]."}
#
# The reported failure identifies missing input data, not a modeling error.
# Three shipping costs per facility do not specify this ten-customer problem.
# Each shipping_cost_f* parameter must contain all ten customer costs.
# Costs for customers 3 through 9 cannot be inferred from "and so on."

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    required_keys = (
        "fixed_cost",
        "demand",
        "capacity",
        "shipping_cost_f0",
        "shipping_cost_f1",
        "shipping_cost_f2",
        "shipping_cost_f3",
    )
    if any(key not in params for key in required_keys):
        return {"objective": None, "status": "missing_parameters"}

    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]
    shipping_rows = (
        params["shipping_cost_f0"],
        params["shipping_cost_f1"],
        params["shipping_cost_f2"],
        params["shipping_cost_f3"],
    )

    if len(fixed_cost) != 4 or len(capacity) != 4 or len(demand) != 10:
        return {"objective": None, "status": "invalid_dimensions"}

    if any(len(row) < 10 for row in shipping_rows):
        return {"objective": None, "status": "missing_shipping_costs"}
    if any(len(row) != 10 for row in shipping_rows):
        return {"objective": None, "status": "invalid_shipping_dimensions"}

    model = pyo.ConcreteModel()
    model.facilities = pyo.RangeSet(0, 3)
    model.customers = pyo.RangeSet(0, 9)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize={f: fixed_cost[f] for f in model.facilities},
        within=pyo.NonNegativeReals,
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
            (f, c): shipping_rows[f][c]
            for f in model.facilities
            for c in model.customers
        },
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.facilities,
        model.customers,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(instance, c):
        return (
            sum(instance.shipment[f, c] for f in instance.facilities)
            == instance.demand[c]
        )

    def capacity_rule(instance, f):
        return (
            sum(instance.shipment[f, c] for c in instance.customers)
            <= instance.capacity[f] * instance.opened[f]
        )

    model.demand_fulfillment = pyo.Constraint(
        model.customers, rule=demand_rule
    )
    model.facility_capacity = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )
    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[f] * model.opened[f]
                for f in model.facilities
            )
            + sum(
                model.shipping_cost[f, c] * model.shipment[f, c]
                for f in model.facilities
                for c in model.customers
            )
        ),
        sense=pyo.minimize,
    )

    solve_error = False
    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when it cannot load a feasible solution.
        solve_error = True

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solver_failed" if solve_error else "objective_unavailable",
        }

    return {"objective": obj_val, "status": "optimal"}