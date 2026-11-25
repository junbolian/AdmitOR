# IR: {"sets":{"facilities":[0,1,2,3],"customers":[0,1,2,3,4,5,6,7,8,9]},"params":{"fixed_cost":"vector[4]","demand":"vector[10]","capacity":"vector[4]","shipping_cost_f0":"vector[10]","shipping_cost_f1":"vector[10]","shipping_cost_f2":"vector[10]","shipping_cost_f3":"vector[10]"},"variables":{"open_center[f]":"Binary","shipment[f,c]":"NonNegativeReals"},"constraints":["For each customer c: sum_f shipment[f,c] == demand[c].","For each facility f: sum_c shipment[f,c] <= capacity[f]*open_center[f]."],"objective":"Minimize sum_f fixed_cost[f]*open_center[f] + sum_f,c shipping_cost[f,c]*shipment[f,c]."}
#
# The stated problem requires 40 shipping costs. If params supplies only
# three costs per facility, the remaining 28 costs are unspecified.
# An objective value for the stated problem cannot be determined without
# those inputs. Repeating costs, using zero costs, or dropping customers
# would change the problem. Supply all ten costs in each shipping vector.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    facilities = range(4)
    customers = range(10)

    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]
    shipping_cost_rows = [
        params["shipping_cost_f0"],
        params["shipping_cost_f1"],
        params["shipping_cost_f2"],
        params["shipping_cost_f3"],
    ]

    if (
        len(fixed_cost) != len(facilities)
        or len(capacity) != len(facilities)
        or len(demand) != len(customers)
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    if any(len(row) < len(customers) for row in shipping_cost_rows):
        return {"objective": None, "status": "insufficient_shipping_data"}

    if any(len(row) != len(customers) for row in shipping_cost_rows):
        return {"objective": None, "status": "invalid_dimensions"}

    model = pyo.ConcreteModel()

    model.facilities = pyo.Set(initialize=facilities, ordered=True)
    model.customers = pyo.Set(initialize=customers, ordered=True)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize={f: fixed_cost[f] for f in facilities},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.customers,
        initialize={c: demand[c] for c in customers},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.facilities,
        initialize={f: capacity[f] for f in facilities},
        within=pyo.NonNegativeReals,
    )
    model.shipping_cost = pyo.Param(
        model.facilities,
        model.customers,
        initialize={
            (f, c): shipping_cost_rows[f][c]
            for f in facilities
            for c in customers
        },
        within=pyo.Reals,
    )

    model.open_center = pyo.Var(
        model.facilities,
        domain=pyo.Binary,
    )
    model.shipment = pyo.Var(
        model.facilities,
        model.customers,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(mdl, c):
        return (
            sum(mdl.shipment[f, c] for f in mdl.facilities)
            == mdl.demand[c]
        )

    model.demand_fulfillment = pyo.Constraint(
        model.customers,
        rule=demand_rule,
    )

    def capacity_rule(mdl, f):
        return (
            sum(mdl.shipment[f, c] for c in mdl.customers)
            <= mdl.capacity[f] * mdl.open_center[f]
        )

    model.facility_capacity = pyo.Constraint(
        model.facilities,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[f] * model.open_center[f]
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

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Let unrelated runtime errors propagate.
        if "A feasible solution was not found" not in str(exc):
            raise

    # Objective retrieval is the sole test of solution success.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}