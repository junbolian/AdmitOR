# IR: {
#   "sets": {"packages": "0..9", "trucks": "0..9"},
#   "params": {"package_weight": "nonnegative real, from params", "truck_capacity": "nonnegative real, from params"},
#   "variables": {"assigned[i,j]": "binary", "truck_used[j]": "binary"},
#   "constraints": [
#     "For each package i: sum_j assigned[i,j] = 1",
#     "For each truck j: package_weight * sum_i assigned[i,j] <= truck_capacity * truck_used[j]",
#     "For each package i and truck j: assigned[i,j] <= truck_used[j]",
#     "For each truck j: truck_used[j] <= sum_i assigned[i,j]"
#   ],
#   "objective": "minimize sum_j truck_used[j]"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.packages = pyo.RangeSet(0, 9)
    model.trucks = pyo.RangeSet(0, 9)

    model.package_weight = pyo.Param(
        initialize=params["package_weight"],
        within=pyo.NonNegativeReals,
    )
    model.truck_capacity = pyo.Param(
        initialize=params["truck_capacity"],
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.packages,
        model.trucks,
        domain=pyo.Binary,
    )
    model.truck_used = pyo.Var(model.trucks, domain=pyo.Binary)

    def assignment_rule(instance, package):
        return sum(
            instance.assigned[package, truck] for truck in instance.trucks
        ) == 1

    model.package_assignment = pyo.Constraint(
        model.packages,
        rule=assignment_rule,
    )

    def capacity_rule(instance, truck):
        return (
            instance.package_weight
            * sum(
                instance.assigned[package, truck]
                for package in instance.packages
            )
            <= instance.truck_capacity * instance.truck_used[truck]
        )

    model.capacity_limit = pyo.Constraint(
        model.trucks,
        rule=capacity_rule,
    )

    def usage_link_rule(instance, package, truck):
        return (
            instance.assigned[package, truck]
            <= instance.truck_used[truck]
        )

    model.usage_link = pyo.Constraint(
        model.packages,
        model.trucks,
        rule=usage_link_rule,
    )

    def nonempty_rule(instance, truck):
        return instance.truck_used[truck] <= sum(
            instance.assigned[package, truck]
            for package in instance.packages
        )

    model.used_truck_nonempty = pyo.Constraint(
        model.trucks,
        rule=nonempty_rule,
    )

    model.total_trucks = pyo.Objective(
        expr=sum(model.truck_used[truck] for truck in model.trucks),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_trucks))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}