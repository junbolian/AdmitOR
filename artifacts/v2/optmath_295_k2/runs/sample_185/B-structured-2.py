# IR: {"sets":{"C":"range(params['num_cities'])","A":"{(i,j) in C x C: i != j}","F":"{(i,j) in A: j != 0}"},"params":{"num_cities":"params['num_cities']","distance[i,j]":"params[f'distance_{i}_{j}'] for (i,j) in A","L":"params['position_lower_bound']","U":"params['position_upper_bound']","M":"U-L+1"},"variables":{"x[i,j]":"binary for (i,j) in A","position[i]":"integer in [L,U] for i in C"},"constraints":["sum(x[i,j] for j in C if j != i) = 1 for i in C","sum(x[i,j] for i in C if i != j) = 1 for j in C","position[0] = L","position[j]-position[i] >= 1-M*(1-x[i,j]) for (i,j) in F","position[j]-position[i] <= 1+M*(1-x[i,j]) for (i,j) in F"],"objective":"minimize sum(distance[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = params["num_cities"]
    position_lower_bound = params["position_lower_bound"]
    position_upper_bound = params["position_upper_bound"]

    cities = list(range(num_cities))
    arcs = [(i, j) for i in cities for j in cities if i != j]
    forward_arcs = [(i, j) for i, j in arcs if j != 0]
    distances = {
        (i, j): params[f"distance_{i}_{j}"]
        for i, j in arcs
    }

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs)
    model.forward_arcs = pyo.Set(dimen=2, initialize=forward_arcs)

    model.distance = pyo.Param(
        model.arcs,
        initialize=distances,
        within=pyo.Reals,
    )
    model.position_lb = pyo.Param(initialize=position_lower_bound)
    model.position_ub = pyo.Param(initialize=position_upper_bound)
    model.sequence_big_m = pyo.Expression(
        expr=model.position_ub - model.position_lb + 1
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.position = pyo.Var(
        model.cities,
        domain=pyo.Integers,
        bounds=(position_lower_bound, position_upper_bound),
    )

    def departure_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.cities if j != i
        ) == 1

    model.departure_once = pyo.Constraint(
        model.cities, rule=departure_rule
    )

    def arrival_rule(instance, j):
        return sum(
            instance.x[i, j] for i in instance.cities if i != j
        ) == 1

    model.arrival_once = pyo.Constraint(
        model.cities, rule=arrival_rule
    )

    model.start_position = pyo.Constraint(
        expr=model.position[0] == model.position_lb
    )

    # Selected arcs advance positions by exactly one, except the return
    # to City 0. This excludes subtours and makes all positions distinct.
    def sequence_lower_rule(instance, i, j):
        return (
            instance.position[j] - instance.position[i]
            >= 1 - instance.sequence_big_m * (1 - instance.x[i, j])
        )

    model.sequence_lower = pyo.Constraint(
        model.forward_arcs, rule=sequence_lower_rule
    )

    def sequence_upper_rule(instance, i, j):
        return (
            instance.position[j] - instance.position[i]
            <= 1 + instance.sequence_big_m * (1 - instance.x[i, j])
        )

    model.sequence_upper = pyo.Constraint(
        model.forward_arcs, rule=sequence_upper_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}