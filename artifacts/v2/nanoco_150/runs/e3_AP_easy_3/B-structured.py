# IR: {"sets":{"advertisers":[0,1,2,3,4],"slots":[0,1,2,3,4]},"params":{"cost_matrix":"params['cost_matrix'][advertiser][slot]"},"variables":{"x[advertiser,slot]":"Binary"},"constraints":["For each advertiser: sum(x[advertiser,slot] for slot in slots) == 1","For each slot: sum(x[advertiser,slot] for advertiser in advertisers) == 1"],"objective":"Minimize sum(cost_matrix[advertiser][slot] * x[advertiser,slot] for advertiser in advertisers for slot in slots)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.advertisers = pyo.RangeSet(0, 4)
    model.slots = pyo.RangeSet(0, 4)

    model.acquisition_cost = pyo.Param(
        model.advertisers,
        model.slots,
        initialize=lambda instance, advertiser, slot: cost_matrix[advertiser][slot],
        within=pyo.Reals,
    )

    model.x = pyo.Var(
        model.advertisers,
        model.slots,
        domain=pyo.Binary,
    )

    def advertiser_assignment_rule(instance, advertiser):
        return sum(instance.x[advertiser, slot] for slot in instance.slots) == 1

    model.advertiser_assignment = pyo.Constraint(
        model.advertisers,
        rule=advertiser_assignment_rule,
    )

    def slot_assignment_rule(instance, slot):
        return (
            sum(instance.x[advertiser, slot] for advertiser in instance.advertisers)
            == 1
        )

    model.slot_assignment = pyo.Constraint(
        model.slots,
        rule=slot_assignment_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.acquisition_cost[advertiser, slot] * model.x[advertiser, slot]
            for advertiser in model.advertisers
            for slot in model.slots
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}