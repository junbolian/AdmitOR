# IR: {"sets":{"goods":"0..5","trucks":"0..5"},"params":{"truck_capacity":"nonnegative scalar from params['truck_capacity']","good_weights":"six nonnegative weights from params['good_weights'] in good order"},"variables":{"x[g,t]":"binary; good g assigned to truck t","y[t]":"binary; truck t used"},"constraints":["For each g: sum_t x[g,t] = 1","For each t: sum_g good_weights[g]*x[g,t] <= truck_capacity*y[t]","For each g,t: x[g,t] <= y[t]"],"objective":"minimize sum_t y[t]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    truck_capacity = params["truck_capacity"]
    good_weights = list(params["good_weights"])

    if len(good_weights) != 6:
        raise ValueError("good_weights must contain exactly six weights.")

    model = pyo.ConcreteModel()

    model.goods = pyo.RangeSet(0, 5)
    model.trucks = pyo.RangeSet(0, 5)

    model.truck_capacity = pyo.Param(
        initialize=truck_capacity,
        within=pyo.NonNegativeReals,
    )
    model.good_weights = pyo.Param(
        model.goods,
        initialize={good: good_weights[good] for good in model.goods},
        within=pyo.NonNegativeReals,
    )

    model.x = pyo.Var(model.goods, model.trucks, domain=pyo.Binary)
    model.y = pyo.Var(model.trucks, domain=pyo.Binary)

    def assignment_rule(instance, good):
        return sum(
            instance.x[good, truck] for truck in instance.trucks
        ) == 1

    model.assignment_constraints = pyo.Constraint(
        model.goods, rule=assignment_rule
    )

    def capacity_rule(instance, truck):
        return sum(
            instance.good_weights[good] * instance.x[good, truck]
            for good in instance.goods
        ) <= instance.truck_capacity * instance.y[truck]

    model.capacity_constraints = pyo.Constraint(
        model.trucks, rule=capacity_rule
    )

    def usage_rule(instance, good, truck):
        return instance.x[good, truck] <= instance.y[truck]

    model.usage_constraints = pyo.Constraint(
        model.goods, model.trucks, rule=usage_rule
    )

    model.total_trucks = pyo.Objective(
        expr=sum(model.y[truck] for truck in model.trucks),
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