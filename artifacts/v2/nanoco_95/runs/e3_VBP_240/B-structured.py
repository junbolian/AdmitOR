# IR: {"sets":{"campaigns":"0..8","slots":"0..8","dimensions":"0..1"},"params":{"capacity":{"source":"params['capacity'][d]","domain":"nonnegative real"},"weights":{"source":"params['weights'][i][d]","domain":"nonnegative real"}},"variables":{"assigned[i,s]":"binary","used[s]":"binary"},"constraints":["For each campaign i: sum_s assigned[i,s] = 1.","For each slot s and dimension d: sum_i weights[i,d]*assigned[i,s] <= capacity[d]*used[s].","For each campaign i and slot s: assigned[i,s] <= used[s]."],"objective":"Minimize sum_s used[s]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.campaigns = pyo.RangeSet(0, 8)
    model.slots = pyo.RangeSet(0, 8)
    model.dimensions = pyo.RangeSet(0, 1)

    model.capacity = pyo.Param(
        model.dimensions,
        initialize=lambda mdl, dim: params["capacity"][dim],
        within=pyo.NonNegativeReals,
    )
    model.weights = pyo.Param(
        model.campaigns,
        model.dimensions,
        initialize=lambda mdl, campaign, dim: params["weights"][campaign][dim],
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.campaigns, model.slots, domain=pyo.Binary
    )
    model.used = pyo.Var(model.slots, domain=pyo.Binary)

    def assignment_rule(mdl, campaign):
        return sum(
            mdl.assigned[campaign, slot] for slot in mdl.slots
        ) == 1

    model.campaign_assignment = pyo.Constraint(
        model.campaigns, rule=assignment_rule
    )

    def capacity_rule(mdl, slot, dim):
        return sum(
            mdl.weights[campaign, dim] * mdl.assigned[campaign, slot]
            for campaign in mdl.campaigns
        ) <= mdl.capacity[dim] * mdl.used[slot]

    model.slot_capacity = pyo.Constraint(
        model.slots, model.dimensions, rule=capacity_rule
    )

    def activation_rule(mdl, campaign, slot):
        return mdl.assigned[campaign, slot] <= mdl.used[slot]

    model.slot_activation = pyo.Constraint(
        model.campaigns, model.slots, rule=activation_rule
    )

    model.total_slots = pyo.Objective(
        expr=sum(model.used[slot] for slot in model.slots),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_slots))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}