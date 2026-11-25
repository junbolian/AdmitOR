# IR: {"sets":{"crates":"1..10","trucks":"1..10"},"params":{"crate_weight":"params['crate_weight']","truck_capacity":"params['truck_capacity']"},"variables":{"assigned[crate,truck]":"Binary","used[truck]":"Binary"},"constraints":["For each crate: sum_truck assigned[crate,truck] = 1","For each truck: crate_weight * sum_crate assigned[crate,truck] <= truck_capacity * used[truck]","For each crate,truck: assigned[crate,truck] <= used[truck]","For each truck: used[truck] <= sum_crate assigned[crate,truck]"],"objective":"Minimize sum_truck used[truck]"}

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

    model.assigned = pyo.Var(
        model.crates, model.trucks, domain=pyo.Binary
    )
    model.used = pyo.Var(model.trucks, domain=pyo.Binary)

    def assignment_rule(instance, crate):
        return sum(
            instance.assigned[crate, truck]
            for truck in instance.trucks
        ) == 1

    model.crate_assignment = pyo.Constraint(
        model.crates, rule=assignment_rule
    )

    def capacity_rule(instance, truck):
        return (
            instance.crate_weight
            * sum(
                instance.assigned[crate, truck]
                for crate in instance.crates
            )
            <= instance.truck_capacity * instance.used[truck]
        )

    model.capacity_limit = pyo.Constraint(
        model.trucks, rule=capacity_rule
    )

    def assignment_requires_use_rule(instance, crate, truck):
        return instance.assigned[crate, truck] <= instance.used[truck]

    model.assignment_requires_use = pyo.Constraint(
        model.crates,
        model.trucks,
        rule=assignment_requires_use_rule,
    )

    def use_requires_assignment_rule(instance, truck):
        return instance.used[truck] <= sum(
            instance.assigned[crate, truck]
            for crate in instance.crates
        )

    model.use_requires_assignment = pyo.Constraint(
        model.trucks, rule=use_requires_assignment_rule
    )

    model.total_trucks = pyo.Objective(
        expr=sum(model.used[truck] for truck in model.trucks),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_trucks))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}