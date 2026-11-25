# IR: {"sets":{"F":"0..9","C":"0..11"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost_f0_c0":"params['cost_f0_c0']","cost_f0_c1":"params['cost_f0_c1']","cost_f1_c0":"params['cost_f1_c0']","cost_f2_c1":"params['cost_f2_c1']","cost_range_low":"params['cost_range_low']","cost_range_high":"params['cost_range_high']"},"cost_definition":"Use the four specified route costs; assume every unspecified route costs (cost_range_low + cost_range_high)/2.","variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["For each i in F: sum_j shipment[i,j] = supply[i].","For each j in C: sum_i shipment[i,j] = demand[j]."],"objective":"Minimize sum_(i,j) cost[i,j] * shipment[i,j]."}
#
# The full route-cost matrix is not supplied. The midpoint assumption above
# completes it explicitly; the resulting optimum is conditional on that assumption.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_f0_c0 = params["cost_f0_c0"]
    cost_f0_c1 = params["cost_f0_c1"]
    cost_f1_c0 = params["cost_f1_c0"]
    cost_f2_c1 = params["cost_f2_c1"]
    cost_range_low = params["cost_range_low"]
    cost_range_high = params["cost_range_high"]

    default_cost = (cost_range_low + cost_range_high) / 2
    specified_costs = {
        (0, 0): cost_f0_c0,
        (0, 1): cost_f0_c1,
        (1, 0): cost_f1_c0,
        (2, 1): cost_f2_c1,
    }

    model = pyo.ConcreteModel()
    model.facilities = pyo.RangeSet(0, 9)
    model.centers = pyo.RangeSet(0, 11)

    model.supply_amount = pyo.Param(
        model.facilities,
        initialize={i: supply[i] for i in model.facilities},
    )
    model.demand_amount = pyo.Param(
        model.centers,
        initialize={j: demand[j] for j in model.centers},
    )
    model.route_cost = pyo.Param(
        model.facilities,
        model.centers,
        initialize={
            (i, j): specified_costs.get((i, j), default_cost)
            for i in model.facilities
            for j in model.centers
        },
    )

    model.shipment = pyo.Var(
        model.facilities,
        model.centers,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.centers)
            == instance.supply_amount[i]
        )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.facilities)
            == instance.demand_amount[j]
        )

    model.supply_balance = pyo.Constraint(
        model.facilities, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.centers, rule=demand_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(
            model.route_cost[i, j] * model.shipment[i, j]
            for i in model.facilities
            for j in model.centers
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