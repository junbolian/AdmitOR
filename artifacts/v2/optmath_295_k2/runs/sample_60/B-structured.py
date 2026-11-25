# IR: {"sets":{"packages":"0..6","trucks":"0..6"},"params":{"package_weights":"weight indexed by package","truck_capacity":"capacity per truck"},"variables":{"assigned[package,truck]":"binary","truck_used[truck]":"binary"},"constraints":["For each package: sum_truck assigned[package,truck] = 1","For each truck: sum_package package_weights[package]*assigned[package,truck] <= truck_capacity*truck_used[truck]","For each package and truck: assigned[package,truck] <= truck_used[truck]","For each truck: sum_package assigned[package,truck] >= truck_used[truck]"],"objective":"minimize sum_truck truck_used[truck]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.packages = pyo.RangeSet(0, 6)
    model.trucks = pyo.RangeSet(0, 6)

    model.package_weight = pyo.Param(
        model.packages,
        initialize=lambda mdl, package: params["package_weights"][package],
    )
    model.capacity = pyo.Param(initialize=params["truck_capacity"])

    model.assigned = pyo.Var(
        model.packages, model.trucks, domain=pyo.Binary
    )
    model.truck_used = pyo.Var(model.trucks, domain=pyo.Binary)

    def package_assignment_rule(mdl, package):
        return sum(
            mdl.assigned[package, truck] for truck in mdl.trucks
        ) == 1

    model.package_assignment = pyo.Constraint(
        model.packages, rule=package_assignment_rule
    )

    def truck_capacity_rule(mdl, truck):
        return sum(
            mdl.package_weight[package] * mdl.assigned[package, truck]
            for package in mdl.packages
        ) <= mdl.capacity * mdl.truck_used[truck]

    model.truck_capacity_limit = pyo.Constraint(
        model.trucks, rule=truck_capacity_rule
    )

    def assignment_requires_truck_rule(mdl, package, truck):
        return mdl.assigned[package, truck] <= mdl.truck_used[truck]

    model.assignment_requires_truck = pyo.Constraint(
        model.packages,
        model.trucks,
        rule=assignment_requires_truck_rule,
    )

    def used_truck_nonempty_rule(mdl, truck):
        return sum(
            mdl.assigned[package, truck] for package in mdl.packages
        ) >= mdl.truck_used[truck]

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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_trucks))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}