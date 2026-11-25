# IR: {
#   "sets": {"campaigns": "1..9", "slots": "1..9"},
#   "params": {"capacity_impressions": "scalar", "capacity_cost": "scalar", "demand_impressions": "length-9 sequence, ordered by campaign", "demand_cost": "length-9 sequence, ordered by campaign"},
#   "variables": {"assigned[i,s]": "binary", "slot_used[s]": "binary"},
#   "constraints": [
#     "For each campaign i: sum_s assigned[i,s] = 1",
#     "For each campaign i and slot s: assigned[i,s] <= slot_used[s]",
#     "For each slot s: sum_i demand_impressions[i] * assigned[i,s] <= capacity_impressions * slot_used[s]",
#     "For each slot s: sum_i demand_cost[i] * assigned[i,s] <= capacity_cost * slot_used[s]"
#   ],
#   "objective": "Minimize sum_s slot_used[s]"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.campaigns = pyo.RangeSet(1, 9)
    model.slots = pyo.RangeSet(1, 9)

    model.capacity_impressions = pyo.Param(
        initialize=params["capacity_impressions"]
    )
    model.capacity_cost = pyo.Param(
        initialize=params["capacity_cost"]
    )
    model.demand_impressions = pyo.Param(
        model.campaigns,
        initialize={
            campaign: params["demand_impressions"][campaign - 1]
            for campaign in model.campaigns
        },
    )
    model.demand_cost = pyo.Param(
        model.campaigns,
        initialize={
            campaign: params["demand_cost"][campaign - 1]
            for campaign in model.campaigns
        },
    )

    model.assigned = pyo.Var(
        model.campaigns, model.slots, domain=pyo.Binary
    )
    model.slot_used = pyo.Var(model.slots, domain=pyo.Binary)

    def assignment_rule(instance, campaign):
        return sum(
            instance.assigned[campaign, slot] for slot in instance.slots
        ) == 1

    model.campaign_assignment = pyo.Constraint(
        model.campaigns, rule=assignment_rule
    )

    def activation_rule(instance, campaign, slot):
        return (
            instance.assigned[campaign, slot] <= instance.slot_used[slot]
        )

    model.slot_activation = pyo.Constraint(
        model.campaigns, model.slots, rule=activation_rule
    )

    def impressions_rule(instance, slot):
        return sum(
            instance.demand_impressions[campaign]
            * instance.assigned[campaign, slot]
            for campaign in instance.campaigns
        ) <= instance.capacity_impressions * instance.slot_used[slot]

    model.impressions_limit = pyo.Constraint(
        model.slots, rule=impressions_rule
    )

    def cost_rule(instance, slot):
        return sum(
            instance.demand_cost[campaign]
            * instance.assigned[campaign, slot]
            for campaign in instance.campaigns
        ) <= instance.capacity_cost * instance.slot_used[slot]

    model.cost_limit = pyo.Constraint(model.slots, rule=cost_rule)

    model.total_slots = pyo.Objective(
        expr=sum(model.slot_used[slot] for slot in model.slots),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_slots))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}