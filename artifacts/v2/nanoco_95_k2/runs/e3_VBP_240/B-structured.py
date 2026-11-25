# IR:
# {
#   "sets": {"campaigns": "1..9", "slots": "1..9"},
#   "params": {
#     "capacity_impressions": "nonnegative scalar from params",
#     "capacity_cost": "nonnegative scalar from params",
#     "demand_impressions": "nonnegative sequence from params, ordered 1..9",
#     "demand_cost": "nonnegative sequence from params, ordered 1..9"
#   },
#   "variables": {
#     "assigned[i,j]": "binary; campaign i assigned to slot j",
#     "used[j]": "binary; slot j activated"
#   },
#   "constraints": [
#     "For each i: sum_j assigned[i,j] = 1",
#     "For each j: sum_i demand_impressions[i] * assigned[i,j] <= capacity_impressions * used[j]",
#     "For each j: sum_i demand_cost[i] * assigned[i,j] <= capacity_cost * used[j]",
#     "For each i,j: assigned[i,j] <= used[j]"
#   ],
#   "objective": "minimize sum_j used[j]"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    # Nine candidate slots suffice for any feasible allocation of nine campaigns.
    model.campaigns = pyo.RangeSet(1, 9)
    model.slots = pyo.RangeSet(1, 9)

    model.capacity_impressions = pyo.Param(
        initialize=params["capacity_impressions"],
        within=pyo.NonNegativeReals,
    )
    model.capacity_cost = pyo.Param(
        initialize=params["capacity_cost"],
        within=pyo.NonNegativeReals,
    )
    model.demand_impressions = pyo.Param(
        model.campaigns,
        initialize={
            campaign: params["demand_impressions"][campaign - 1]
            for campaign in model.campaigns
        },
        within=pyo.NonNegativeReals,
    )
    model.demand_cost = pyo.Param(
        model.campaigns,
        initialize={
            campaign: params["demand_cost"][campaign - 1]
            for campaign in model.campaigns
        },
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.campaigns, model.slots, domain=pyo.Binary
    )
    model.used = pyo.Var(model.slots, domain=pyo.Binary)

    def assignment_rule(block, campaign):
        return sum(
            block.assigned[campaign, slot] for slot in block.slots
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.campaigns, rule=assignment_rule
    )

    def impressions_rule(block, slot):
        return sum(
            block.demand_impressions[campaign]
            * block.assigned[campaign, slot]
            for campaign in block.campaigns
        ) <= block.capacity_impressions * block.used[slot]

    model.impressions_constraints = pyo.Constraint(
        model.slots, rule=impressions_rule
    )

    def cost_rule(block, slot):
        return sum(
            block.demand_cost[campaign] * block.assigned[campaign, slot]
            for campaign in block.campaigns
        ) <= block.capacity_cost * block.used[slot]

    model.cost_constraints = pyo.Constraint(
        model.slots, rule=cost_rule
    )

    def activation_rule(block, campaign, slot):
        return block.assigned[campaign, slot] <= block.used[slot]

    model.activation_constraints = pyo.Constraint(
        model.campaigns, model.slots, rule=activation_rule
    )

    model.total_slots = pyo.Objective(
        expr=sum(model.used[slot] for slot in model.slots),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_slots))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}