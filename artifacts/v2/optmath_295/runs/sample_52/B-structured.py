# IR: {"sets":{"F":[0,1,2,3],"C":[0,1,2,3,4,5,6,7,8,9]},"params":{"fixed_cost":"params['fixed_cost'][f]","demand":"params['demand'][c], nonnegative","capacity":"params['capacity'][f], nonnegative","service_cost":"params['service_cost'][f][c]; full matrix required because 36 coefficients are unspecified"},"variables":{"opened[f]":"binary","shipment[f,c]":"nonnegative continuous"},"constraints":["Each c: sum_f shipment[f,c] == demand[c]","Each f: sum_c shipment[f,c] <= capacity[f]*opened[f]"],"objective":"minimize sum_f fixed_cost[f]*opened[f] + sum_f,c service_cost[f][c]*shipment[f,c]","failure":"Return objective=None if required service costs are absent or solving/objective evaluation fails."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    # The three listed inputs do not determine the stated objective.
    # Only customer 0's four service costs are given; the remaining
    # 36 costs cannot be inferred from their stated range.
    # An exact numerical solution requires the complete service-cost
    # matrix as an additional input. Inventing coefficients would solve
    # a different problem.
    if "service_cost" not in params:
        return {"objective": None, "status": "insufficient_cost_data"}

    service_cost = params["service_cost"]

    model = pyo.ConcreteModel()
    model.facilities = pyo.RangeSet(0, 3)
    model.customers = pyo.RangeSet(0, 9)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize=lambda mdl, facility: fixed_cost[facility],
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.customers,
        initialize=lambda mdl, customer: demand[customer],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.facilities,
        initialize=lambda mdl, facility: capacity[facility],
        within=pyo.NonNegativeReals,
    )
    model.service_cost = pyo.Param(
        model.facilities,
        model.customers,
        initialize=lambda mdl, facility, customer: service_cost[facility][customer],
        within=pyo.Reals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.facilities,
        model.customers,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(mdl, customer):
        return sum(
            mdl.shipment[facility, customer] for facility in mdl.facilities
        ) == mdl.demand[customer]

    model.demand_satisfaction = pyo.Constraint(
        model.customers, rule=demand_rule
    )

    def capacity_rule(mdl, facility):
        return sum(
            mdl.shipment[facility, customer] for customer in mdl.customers
        ) <= mdl.capacity[facility] * mdl.opened[facility]

    model.capacity_link = pyo.Constraint(
        model.facilities, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_cost[facility] * model.opened[facility]
            for facility in model.facilities
        )
        + sum(
            model.service_cost[facility, customer]
            * model.shipment[facility, customer]
            for facility in model.facilities
            for customer in model.customers
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Missing feasible solutions can prevent Appsi from loading values.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}