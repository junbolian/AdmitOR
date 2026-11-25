# IR: {"sets":{"C":"range(num_crates)","T":"range(num_trucks)"},"params":{"crate_weight":"nonnegative real","truck_capacity":"nonnegative real","num_crates":"nonnegative integer","num_trucks":"nonnegative integer"},"variables":{"x[c,t]":"binary; crate c assigned to truck t","y[t]":"binary; truck t used"},"constraints":["sum(x[c,t] for t in T) = 1 for each c in C","crate_weight * sum(x[c,t] for c in C) <= truck_capacity * y[t] for each t in T","x[c,t] <= y[t] for each (c,t) in C x T","y[t] <= sum(x[c,t] for c in C) for each t in T"],"objective":"minimize sum(y[t] for t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.num_crates = pyo.Param(
        initialize=params["num_crates"],
        within=pyo.NonNegativeIntegers,
    )
    model.num_trucks = pyo.Param(
        initialize=params["num_trucks"],
        within=pyo.NonNegativeIntegers,
    )
    model.crate_weight = pyo.Param(
        initialize=params["crate_weight"],
        within=pyo.NonNegativeReals,
    )
    model.truck_capacity = pyo.Param(
        initialize=params["truck_capacity"],
        within=pyo.NonNegativeReals,
    )

    model.C = pyo.Set(
        initialize=range(int(pyo.value(model.num_crates))),
        ordered=True,
    )
    model.T = pyo.Set(
        initialize=range(int(pyo.value(model.num_trucks))),
        ordered=True,
    )

    model.x = pyo.Var(model.C, model.T, domain=pyo.Binary)
    model.y = pyo.Var(model.T, domain=pyo.Binary)

    def assignment_rule(instance, crate):
        return (
            1,
            pyo.quicksum(instance.x[crate, truck] for truck in instance.T),
            1,
        )

    model.crate_assignment = pyo.Constraint(
        model.C,
        rule=assignment_rule,
    )

    def capacity_rule(instance, truck):
        return (
            instance.crate_weight
            * pyo.quicksum(instance.x[crate, truck] for crate in instance.C)
            <= instance.truck_capacity * instance.y[truck]
        )

    model.truck_capacity_limit = pyo.Constraint(
        model.T,
        rule=capacity_rule,
    )

    def assignment_usage_rule(instance, crate, truck):
        return instance.x[crate, truck] <= instance.y[truck]

    model.assignment_requires_usage = pyo.Constraint(
        model.C,
        model.T,
        rule=assignment_usage_rule,
    )

    def usage_requires_load_rule(instance, truck):
        return instance.y[truck] <= pyo.quicksum(
            instance.x[crate, truck] for crate in instance.C
        )

    model.usage_requires_load = pyo.Constraint(
        model.T,
        rule=usage_requires_load_rule,
    )

    model.trucks_used = pyo.Objective(
        expr=pyo.quicksum(model.y[truck] for truck in model.T),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS may raise when no feasible solution can be loaded.
        # Objective retrieval below is the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.trucks_used))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}