# IR: {"sets":{"packages":"0..6","trucks":"0..6"},"params":{"package_weights":"weight indexed by package","truck_capacity":"capacity per truck"},"variables":{"assigned[p,t]":"binary","truck_used[t]":"binary"},"constraints":["For each package p: sum_t assigned[p,t] = 1","For each truck t: sum_p package_weights[p]*assigned[p,t] <= truck_capacity*truck_used[t]","For each package p and truck t: assigned[p,t] <= truck_used[t]","For each truck t: truck_used[t] <= sum_p assigned[p,t]"],"objective":"minimize sum_t truck_used[t]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.packages = pyo.RangeSet(0, 6)
    model.trucks = pyo.RangeSet(0, 6)

    model.package_weights = pyo.Param(
        model.packages,
        initialize={
            package: params["package_weights"][package]
            for package in model.packages
        },
        within=pyo.NonNegativeReals,
    )
    model.truck_capacity = pyo.Param(
        initialize=params["truck_capacity"],
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.packages, model.trucks, domain=pyo.Binary
    )
    model.truck_used = pyo.Var(model.trucks, domain=pyo.Binary)

    def package_assignment_rule(current_model, package):
        return sum(
            current_model.assigned[package, truck]
            for truck in current_model.trucks
        ) == 1

    model.package_assignment = pyo.Constraint(
        model.packages, rule=package_assignment_rule
    )

    def capacity_rule(current_model, truck):
        return sum(
            current_model.package_weights[package]
            * current_model.assigned[package, truck]
            for package in current_model.packages
        ) <= current_model.truck_capacity * current_model.truck_used[truck]

    model.capacity_limit = pyo.Constraint(
        model.trucks, rule=capacity_rule
    )

    def assignment_requires_truck_rule(current_model, package, truck):
        return (
            current_model.assigned[package, truck]
            <= current_model.truck_used[truck]
        )

    model.assignment_requires_truck = pyo.Constraint(
        model.packages,
        model.trucks,
        rule=assignment_requires_truck_rule,
    )

    def used_truck_nonempty_rule(current_model, truck):
        return current_model.truck_used[truck] <= sum(
            current_model.assigned[package, truck]
            for package in current_model.packages
        )

    model.used_truck_nonempty = pyo.Constraint(
        model.trucks, rule=used_truck_nonempty_rule
    )

    model.total_trucks = pyo.Objective(
        expr=sum(model.truck_used[truck] for truck in model.trucks),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_trucks))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}