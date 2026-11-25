# IR: {"sets":{"goods":[1,2,3,4,5,6],"trucks":[1,2,3,4,5,6]},"params":{"truck_capacity":"params['truck_capacity']","good_weights":"params['good_weights'], ordered goods 1 through 6"},"variables":{"assigned[g,t]":"binary","used[t]":"binary"},"constraints":["For each good g: sum_t assigned[g,t] = 1","For each truck t: sum_g good_weights[g]*assigned[g,t] <= truck_capacity*used[t]","For each good g and truck t: assigned[g,t] <= used[t]"],"objective":"minimize sum_t used[t]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.goods = pyo.RangeSet(1, 6)
    model.trucks = pyo.RangeSet(1, 6)

    model.truck_capacity = pyo.Param(
        initialize=params["truck_capacity"]
    )
    model.good_weights = pyo.Param(
        model.goods,
        initialize={
            good: params["good_weights"][good - 1]
            for good in model.goods
        },
    )

    model.assigned = pyo.Var(
        model.goods, model.trucks, domain=pyo.Binary
    )
    model.used = pyo.Var(model.trucks, domain=pyo.Binary)

    def assignment_rule(instance, good):
        return sum(
            instance.assigned[good, truck]
            for truck in instance.trucks
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.goods, rule=assignment_rule
    )

    def capacity_rule(instance, truck):
        return sum(
            instance.good_weights[good] * instance.assigned[good, truck]
            for good in instance.goods
        ) <= instance.truck_capacity * instance.used[truck]

    model.capacity_constraints = pyo.Constraint(
        model.trucks, rule=capacity_rule
    )

    def usage_rule(instance, good, truck):
        return instance.assigned[good, truck] <= instance.used[truck]

    model.usage_constraints = pyo.Constraint(
        model.goods, model.trucks, rule=usage_rule
    )

    model.total_trucks = pyo.Objective(
        expr=sum(model.used[truck] for truck in model.trucks),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        if "a feasible solution was not found" not in str(error).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_trucks))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}