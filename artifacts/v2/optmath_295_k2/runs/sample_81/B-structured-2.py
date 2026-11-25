# IR: {"sets":{"crates":"1..10","trucks":"1..10"},"params":{"crate_weight":"nonnegative real from params","truck_capacity":"nonnegative real from params"},"variables":{"assigned[crate,truck]":"binary","truck_used[truck]":"binary"},"constraints":["For each crate: sum_truck assigned[crate,truck] = 1","For each truck: crate_weight * sum_crate assigned[crate,truck] <= truck_capacity * truck_used[truck]","For each crate,truck: assigned[crate,truck] <= truck_used[truck]","For each truck: truck_used[truck] <= sum_crate assigned[crate,truck]"],"objective":"Minimize sum_truck truck_used[truck]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.crates = pyo.RangeSet(1, 10)
    model.trucks = pyo.RangeSet(1, 10)

    model.crate_weight = pyo.Param(
        initialize=params["crate_weight"],
        within=pyo.NonNegativeReals,
    )
    model.truck_capacity = pyo.Param(
        initialize=params["truck_capacity"],
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(model.crates, model.trucks, domain=pyo.Binary)
    model.truck_used = pyo.Var(model.trucks, domain=pyo.Binary)

    def assignment_rule(model, crate):
        return sum(
            model.assigned[crate, truck] for truck in model.trucks
        ) == 1

    model.crate_assignment = pyo.Constraint(
        model.crates,
        rule=assignment_rule,
    )

    def capacity_rule(model, truck):
        return (
            model.crate_weight
            * sum(model.assigned[crate, truck] for crate in model.crates)
            <= model.truck_capacity * model.truck_used[truck]
        )

    model.capacity_limit = pyo.Constraint(model.trucks, rule=capacity_rule)

    def assignment_requires_truck_rule(model, crate, truck):
        return model.assigned[crate, truck] <= model.truck_used[truck]

    model.assignment_requires_truck = pyo.Constraint(
        model.crates,
        model.trucks,
        rule=assignment_requires_truck_rule,
    )

    def used_truck_nonempty_rule(model, truck):
        return model.truck_used[truck] <= sum(
            model.assigned[crate, truck] for crate in model.crates
        )

    model.used_truck_nonempty = pyo.Constraint(
        model.trucks,
        rule=used_truck_nonempty_rule,
    )

    model.total_trucks = pyo.Objective(
        expr=sum(model.truck_used[truck] for truck in model.trucks),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_trucks))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}