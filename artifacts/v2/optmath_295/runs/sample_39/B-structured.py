# IR: {"sets":{"packages":"{0,1,2,3,4}","trucks":"range(params['num_available_trucks'])"},"params":{"package_weights":"params['package_weights'][i] for i in packages, nonnegative","truck_capacity":"params['truck_capacity'], nonnegative","num_available_trucks":"params['num_available_trucks'], nonnegative integer; fixed fleet size"},"variables":{"assignment[i,t]":"binary","truck_used[t]":"binary"},"constraints":["For each package i: sum_t assignment[i,t] = 1.","For each truck t: sum_i package_weights[i]*assignment[i,t] <= truck_capacity*truck_used[t].","For each package i and truck t: assignment[i,t] <= truck_used[t].","For each truck t: truck_used[t] <= sum_i assignment[i,t]."],"objective":"Minimize sum_t truck_used[t]."}

import operator

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    package_weights = params["package_weights"]
    truck_capacity = params["truck_capacity"]
    num_available_trucks = operator.index(params["num_available_trucks"])

    if num_available_trucks < 0:
        raise ValueError("num_available_trucks must be nonnegative.")

    model = pyo.ConcreteModel()

    model.packages = pyo.Set(initialize=range(5), ordered=True)
    model.trucks = pyo.Set(
        initialize=range(num_available_trucks),
        ordered=True,
    )

    model.package_weights = pyo.Param(
        model.packages,
        initialize={
            package: package_weights[package]
            for package in model.packages
        },
        within=pyo.NonNegativeReals,
    )
    model.truck_capacity = pyo.Param(
        initialize=truck_capacity,
        within=pyo.NonNegativeReals,
    )
    model.num_available_trucks = pyo.Param(
        initialize=num_available_trucks,
        within=pyo.NonNegativeIntegers,
    )

    model.assignment = pyo.Var(
        model.packages,
        model.trucks,
        domain=pyo.Binary,
    )
    model.truck_used = pyo.Var(model.trucks, domain=pyo.Binary)

    def assignment_rule(instance, package):
        # Tuple form also represents infeasibility for an empty fleet.
        return (
            1,
            pyo.quicksum(
                instance.assignment[package, truck]
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
                instance.package_weights[package]
                * instance.assignment[package, truck]
                for package in instance.packages
            )
            <= instance.truck_capacity * instance.truck_used[truck]
        )

    model.truck_capacity_limit = pyo.Constraint(
        model.trucks,
        rule=capacity_rule,
    )

    def assignment_requires_use_rule(instance, package, truck):
        return (
            instance.assignment[package, truck]
            <= instance.truck_used[truck]
        )

    model.assignment_requires_use = pyo.Constraint(
        model.packages,
        model.trucks,
        rule=assignment_requires_use_rule,
    )

    def used_truck_has_package_rule(instance, truck):
        return instance.truck_used[truck] <= pyo.quicksum(
            instance.assignment[package, truck]
            for package in instance.packages
        )

    model.used_truck_has_package = pyo.Constraint(
        model.trucks,
        rule=used_truck_has_package_rule,
    )

    model.total_trucks_used = pyo.Objective(
        expr=pyo.quicksum(
            model.truck_used[truck] for truck in model.trucks
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_trucks_used))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}