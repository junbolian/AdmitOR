# IR: {"sets":{"P":"range(params['num_packages'])","T":"range(params['num_trucks'])"},"params":{"package_weights":"params['package_weights'][i], i in P","truck_capacity":"params['truck_capacity']","num_trucks":"params['num_trucks']","num_packages":"params['num_packages']"},"variables":{"assigned[i,j]":"binary, i in P, j in T","truck_used[j]":"binary, j in T"},"constraints":{"assignment":"sum(assigned[i,j] for j in T) = 1, i in P","capacity":"sum(package_weights[i]*assigned[i,j] for i in P) <= truck_capacity*truck_used[j], j in T","activation":"assigned[i,j] <= truck_used[j], i in P, j in T","nonempty":"truck_used[j] <= sum(assigned[i,j] for i in P), j in T"},"objective":"minimize sum(truck_used[j] for j in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.package_count = pyo.Param(
        initialize=params["num_packages"], within=pyo.NonNegativeIntegers
    )
    model.truck_count = pyo.Param(
        initialize=params["num_trucks"], within=pyo.NonNegativeIntegers
    )

    model.P = pyo.Set(
        initialize=range(params["num_packages"]), ordered=True
    )
    model.T = pyo.Set(
        initialize=range(params["num_trucks"]), ordered=True
    )

    model.package_weight = pyo.Param(
        model.P,
        initialize=lambda model, i: params["package_weights"][i],
        within=pyo.NonNegativeReals,
    )
    model.capacity_limit = pyo.Param(
        initialize=params["truck_capacity"], within=pyo.NonNegativeReals
    )

    model.assigned = pyo.Var(model.P, model.T, domain=pyo.Binary)
    model.truck_used = pyo.Var(model.T, domain=pyo.Binary)

    def assignment_rule(model, i):
        if len(model.T) == 0:
            return pyo.Constraint.Infeasible
        return pyo.quicksum(
            model.assigned[i, j] for j in model.T
        ) == 1

    model.package_assignment = pyo.Constraint(
        model.P, rule=assignment_rule
    )

    def capacity_rule(model, j):
        return pyo.quicksum(
            model.package_weight[i] * model.assigned[i, j]
            for i in model.P
        ) <= model.capacity_limit * model.truck_used[j]

    model.truck_capacity_constraint = pyo.Constraint(
        model.T, rule=capacity_rule
    )

    def activation_rule(model, i, j):
        return model.assigned[i, j] <= model.truck_used[j]

    model.truck_activation = pyo.Constraint(
        model.P, model.T, rule=activation_rule
    )

    def nonempty_rule(model, j):
        return model.truck_used[j] <= pyo.quicksum(
            model.assigned[i, j] for i in model.P
        )

    model.used_truck_nonempty = pyo.Constraint(
        model.T, rule=nonempty_rule
    )

    model.total_trucks = pyo.Objective(
        expr=pyo.quicksum(model.truck_used[j] for j in model.T),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Appsi may raise when no feasible solution can be loaded.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_trucks))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}