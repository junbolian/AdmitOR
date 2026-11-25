# IR: {"sets":{"V":"{0,...,6}","A":"{(i,j) in V x V: i != j}","B":"{(i,j) in A: j != 0}"},"params":{"cost":"params['cost'][i][j] for (i,j) in A"},"variables":{"x[i,j]":"Binary for (i,j) in A","u[i]":"Integer; u[0]=0; 1 <= u[i] <= 6 for i != 0"},"constraints":["sum(x[i,j] for j != i) = 1 for every i in V","sum(x[i,j] for i != j) = 1 for every j in V","u[j] >= u[i] + 1 - 7*(1-x[i,j]) for every (i,j) in B; together with degree constraints, this excludes subtours and implies distinct nondepot positions"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost"]
    city_count = 7

    model = pyo.ConcreteModel()
    model.cities = pyo.RangeSet(0, city_count - 1)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(city_count)
            for j in range(city_count)
            if i != j
        ],
    )
    model.forward_arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(city_count)
            for j in range(1, city_count)
            if i != j
        ],
    )

    model.arc_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): cost_matrix[i][j]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.route_used = pyo.Var(model.arcs, domain=pyo.Binary)

    def position_bounds(instance, city):
        if city == 0:
            return (0, 0)
        return (1, city_count - 1)

    model.position = pyo.Var(
        model.cities,
        domain=pyo.Integers,
        bounds=position_bounds,
    )
    model.position[0].fix(0)

    def outgoing_rule(instance, city):
        return sum(
            instance.route_used[city, destination]
            for destination in instance.cities
            if destination != city
        ) == 1

    model.outgoing_once = pyo.Constraint(
        model.cities, rule=outgoing_rule
    )

    def incoming_rule(instance, city):
        return sum(
            instance.route_used[origin, city]
            for origin in instance.cities
            if origin != city
        ) == 1

    model.incoming_once = pyo.Constraint(
        model.cities, rule=incoming_rule
    )

    def sequence_rule(instance, origin, destination):
        return (
            instance.position[destination]
            >= instance.position[origin]
            + 1
            - city_count * (1 - instance.route_used[origin, destination])
        )

    model.sequence_order = pyo.Constraint(
        model.forward_arcs, rule=sequence_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.arc_cost[i, j] * model.route_used[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}