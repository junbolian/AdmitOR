# IR: {"sets":{"P":"0..6","T":"0..max_trucks-1"},"params":{"package_weights":"weight[p] for p in P","truck_capacity":"capacity per truck","max_trucks":"available truck count"},"variables":{"x[p,t]":"binary; package p assigned to truck t","y[t]":"binary; truck t used"},"constraints":["sum(x[p,t] for t in T) = 1 for each p in P","sum(package_weights[p]*x[p,t] for p in P) <= truck_capacity*y[t] for each t in T","x[p,t] <= y[t] for each p in P, t in T"],"objective":"minimize sum(y[t] for t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    package_weights = params["package_weights"]
    truck_capacity = params["truck_capacity"]
    max_trucks = params["max_trucks"]

    model = pyo.ConcreteModel()

    model.packages = pyo.Set(initialize=range(7), ordered=True)
    model.trucks = pyo.Set(initialize=range(max_trucks), ordered=True)

    model.weight = pyo.Param(
        model.packages,
        initialize={pkg: package_weights[pkg] for pkg in range(7)},
    )
    model.capacity = pyo.Param(initialize=truck_capacity)

    model.assignment = pyo.Var(
        model.packages, model.trucks, domain=pyo.Binary
    )
    model.truck_used = pyo.Var(model.trucks, domain=pyo.Binary)

    def assignment_rule(model, pkg):
        return (
            sum(model.assignment[pkg, truck] for truck in model.trucks)
            == 1
        )

    model.package_assignment = pyo.Constraint(
        model.packages, rule=assignment_rule
    )

    def capacity_rule(model, truck):
        return (
            sum(
                model.weight[pkg] * model.assignment[pkg, truck]
                for pkg in model.packages
            )
            <= model.capacity * model.truck_used[truck]
        )

    model.truck_capacity_limit = pyo.Constraint(
        model.trucks, rule=capacity_rule
    )

    def usage_rule(model, pkg, truck):
        return model.assignment[pkg, truck] <= model.truck_used[truck]

    model.assignment_requires_truck = pyo.Constraint(
        model.packages, model.trucks, rule=usage_rule
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
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}