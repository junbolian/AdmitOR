# IR: {"sets":{"goods":[1,2,3,4,5,6],"trucks":[1,2,3,4,5,6]},"params":{"truck_capacity":"nonnegative real from params['truck_capacity']","good_weights":"six nonnegative real weights from params['good_weights'], ordered by good"},"variables":{"assigned[good,truck]":"binary","truck_used[truck]":"binary"},"constraints":["For each good: sum(assigned[good,truck] for truck in trucks) == 1","For each truck: sum(good_weights[good]*assigned[good,truck] for good in goods) <= truck_capacity*truck_used[truck]","For each good and truck: assigned[good,truck] <= truck_used[truck]"],"objective":"minimize sum(truck_used[truck] for truck in trucks)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["truck_capacity"]
    weights = params["good_weights"]

    if len(weights) != 6:
        raise ValueError("good_weights must contain exactly six weights.")

    model = pyo.ConcreteModel()

    model.goods = pyo.RangeSet(1, 6)
    model.trucks = pyo.RangeSet(1, 6)

    model.truck_capacity = pyo.Param(
        initialize=capacity,
        within=pyo.NonNegativeReals,
    )
    model.good_weights = pyo.Param(
        model.goods,
        initialize={good: weights[good - 1] for good in model.goods},
        within=pyo.NonNegativeReals,
    )

    model.assigned = pyo.Var(
        model.goods,
        model.trucks,
        domain=pyo.Binary,
    )
    model.truck_used = pyo.Var(model.trucks, domain=pyo.Binary)

    def assignment_rule(instance, good):
        return sum(
            instance.assigned[good, truck] for truck in instance.trucks
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.goods,
        rule=assignment_rule,
    )

    def capacity_rule(instance, truck):
        return sum(
            instance.good_weights[good] * instance.assigned[good, truck]
            for good in instance.goods
        ) <= instance.truck_capacity * instance.truck_used[truck]

    model.capacity_constraints = pyo.Constraint(
        model.trucks,
        rule=capacity_rule,
    )

    def usage_rule(instance, good, truck):
        return instance.assigned[good, truck] <= instance.truck_used[truck]

    model.usage_constraints = pyo.Constraint(
        model.goods,
        model.trucks,
        rule=usage_rule,
    )

    model.total_trucks = pyo.Objective(
        expr=sum(model.truck_used[truck] for truck in model.trucks),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_trucks))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}