# IR: {"sets":{"P":"range(5)","T":"range(params['num_trucks'])"},"params":{"package_weights":"params['package_weights'][i], i in P","truck_capacity":"params['truck_capacity']","num_trucks":"params['num_trucks']"},"variables":{"assigned[i,t]":"Binary, i in P, t in T","used[t]":"Binary, t in T"},"constraints":["sum(assigned[i,t] for t in T) == 1, i in P","sum(package_weights[i]*assigned[i,t] for i in P) <= truck_capacity*used[t], t in T","assigned[i,t] <= used[t], i in P, t in T","used[t] <= sum(assigned[i,t] for i in P), t in T"],"objective":"minimize sum(used[t] for t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.packages = pyo.Set(initialize=range(5), ordered=True)
    model.trucks = pyo.Set(
        initialize=range(params["num_trucks"]),
        ordered=True,
    )

    model.package_weight = pyo.Param(
        model.packages,
        initialize={
            package: params["package_weights"][package]
            for package in model.packages
        },
    )
    model.capacity = pyo.Param(initialize=params["truck_capacity"])

    model.assigned = pyo.Var(
        model.packages,
        model.trucks,
        domain=pyo.Binary,
    )
    model.used = pyo.Var(model.trucks, domain=pyo.Binary)

    def assignment_rule(instance, package):
        # The tuple form also supports an empty truck index set.
        return (
            1,
            pyo.quicksum(
                instance.assigned[package, truck]
                for truck in instance.trucks
            ),
            1,
        )

    model.package_assignment = pyo.Constraint(
        model.packages,
        rule=assignment_rule,
    )

    def capacity_rule(instance, truck):
        return (
            pyo.quicksum(
                instance.package_weight[package]
                * instance.assigned[package, truck]
                for package in instance.packages
            )
            <= instance.capacity * instance.used[truck]
        )

    model.truck_capacity_limit = pyo.Constraint(
        model.trucks,
        rule=capacity_rule,
    )

    def assignment_requires_use_rule(instance, package, truck):
        return instance.assigned[package, truck] <= instance.used[truck]

    model.assignment_requires_use = pyo.Constraint(
        model.packages,
        model.trucks,
        rule=assignment_requires_use_rule,
    )

    def use_requires_package_rule(instance, truck):
        return instance.used[truck] <= pyo.quicksum(
            instance.assigned[package, truck]
            for package in instance.packages
        )

    model.use_requires_package = pyo.Constraint(
        model.trucks,
        rule=use_requires_package_rule,
    )

    model.total_trucks = pyo.Objective(
        expr=pyo.quicksum(model.used[truck] for truck in model.trucks),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # Appsi raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_trucks))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}