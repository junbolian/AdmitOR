# IR: {"sets":{"P":"{0,1,2,3,4}","T":"range(params['num_trucks'])"},"params":{"package_weights":"params['package_weights'][i], i in P","truck_capacity":"params['truck_capacity']","num_trucks":"params['num_trucks'] (frozen index-set size)"},"variables":{"assigned[i,t]":"binary, i in P, t in T","used[t]":"binary, t in T"},"constraints":["sum(assigned[i,t] for t in T) == 1, for each i in P","sum(package_weights[i]*assigned[i,t] for i in P) <= truck_capacity*used[t], for each t in T","assigned[i,t] <= used[t], for each i in P, t in T","used[t] <= sum(assigned[i,t] for i in P), for each t in T"],"objective":"minimize sum(used[t] for t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    package_weights = params["package_weights"]
    truck_capacity = params["truck_capacity"]
    num_trucks = params["num_trucks"]

    model = pyo.ConcreteModel()
    model.packages = pyo.Set(initialize=range(5), ordered=True)
    model.trucks = pyo.Set(initialize=range(num_trucks), ordered=True)

    model.package_weight = pyo.Param(
        model.packages,
        initialize={i: package_weights[i] for i in model.packages},
    )
    model.capacity_limit = pyo.Param(initialize=truck_capacity)

    model.assigned = pyo.Var(
        model.packages, model.trucks, domain=pyo.Binary
    )
    model.used = pyo.Var(model.trucks, domain=pyo.Binary)

    def assignment_rule(block, i):
        # The tuple form also handles an empty truck set.
        return (
            1,
            pyo.quicksum(block.assigned[i, t] for t in block.trucks),
            1,
        )

    model.package_assignment = pyo.Constraint(
        model.packages, rule=assignment_rule
    )

    def capacity_rule(block, t):
        return (
            pyo.quicksum(
                block.package_weight[i] * block.assigned[i, t]
                for i in block.packages
            )
            <= block.capacity_limit * block.used[t]
        )

    model.truck_capacity_constraint = pyo.Constraint(
        model.trucks, rule=capacity_rule
    )

    def activation_rule(block, i, t):
        return block.assigned[i, t] <= block.used[t]

    model.assignment_activation = pyo.Constraint(
        model.packages, model.trucks, rule=activation_rule
    )

    def nonempty_rule(block, t):
        return block.used[t] <= pyo.quicksum(
            block.assigned[i, t] for i in block.packages
        )

    model.used_truck_nonempty = pyo.Constraint(
        model.trucks, rule=nonempty_rule
    )

    model.total_trucks = pyo.Objective(
        expr=pyo.quicksum(model.used[t] for t in model.trucks),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_trucks))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}