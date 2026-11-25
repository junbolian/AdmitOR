# IR: {"sets":{"I":[0,1,2,3,4],"J":[0,1,2,3,4,5,6]},"params":{"fixed_costs":"I -> real","shipping_costs":"I x J -> real","demands":"J -> nonnegative real","capacities":"I -> nonnegative real"},"variables":{"opened[i]":"binary, i in I","shipment[i,j]":"nonnegative real, (i,j) in I x J"},"constraints":["sum(shipment[i,j] for i in I) == demands[j], j in J","sum(shipment[i,j] for j in J) <= capacities[i]*opened[i], i in I"],"objective":"minimize sum(fixed_costs[i]*opened[i] for i in I) + sum(shipping_costs[i,j]*shipment[i,j] for i in I for j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, 4)
    model.J = pyo.RangeSet(0, 6)

    model.fixed_costs = pyo.Param(
        model.I,
        initialize=lambda mdl, i: params["fixed_costs"][i],
        within=pyo.Reals,
    )
    model.shipping_costs = pyo.Param(
        model.I,
        model.J,
        initialize=lambda mdl, i, j: params["shipping_costs"][i][j],
        within=pyo.Reals,
    )
    model.demands = pyo.Param(
        model.J,
        initialize=lambda mdl, j: params["demands"][j],
        within=pyo.NonNegativeReals,
    )
    model.capacities = pyo.Param(
        model.I,
        initialize=lambda mdl, i: params["capacities"][i],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.I, domain=pyo.Binary)
    model.shipment = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def demand_rule(mdl, j):
        return sum(mdl.shipment[i, j] for i in mdl.I) == mdl.demands[j]

    model.demand_satisfaction = pyo.Constraint(model.J, rule=demand_rule)

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.J)
            <= mdl.capacities[i] * mdl.opened[i]
        )

    model.capacity_activation = pyo.Constraint(model.I, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.fixed_costs[i] * model.opened[i]
            for i in model.I
        )
        + sum(
            model.shipping_costs[i, j] * model.shipment[i, j]
            for i in model.I
            for j in model.J
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}