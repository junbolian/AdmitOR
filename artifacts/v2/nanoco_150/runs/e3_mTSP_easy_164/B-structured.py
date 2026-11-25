# IR: {"sets":{"V":"0..8","C":"1..8","A":"{(i,j) in V x V: i != j}","S":"{(i,j) in C x C: i != j}"},"params":{"distance_matrix":"params['distance_matrix'], indexed by V x V","fleet_size":"params['fleet_size'], nonnegative integer"},"variables":{"x[i,j]":"binary for (i,j) in A; selected directed arc","u[i]":"continuous in [1,|C|] for i in C"},"constraints":["For each i in C: sum(x[i,j] for j in V if j != i) = 1","For each j in C: sum(x[i,j] for i in V if i != j) = 1","sum(x[0,j] for j in C) = fleet_size","sum(x[i,0] for i in C) = fleet_size","For each (i,j) in S: u[i] - u[j] + |C|*x[i,j] <= |C|-1"],"objective":"Minimize sum(distance_matrix[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.V = pyo.RangeSet(0, 8)
    model.C = pyo.RangeSet(1, 8)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.V
            for j in model.V
            if i != j
        ],
    )
    model.S = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in model.C
            for j in model.C
            if i != j
        ],
    )

    model.distance_matrix = pyo.Param(
        model.V,
        model.V,
        initialize={
            (i, j): params["distance_matrix"][i][j]
            for i in model.V
            for j in model.V
        },
        within=pyo.NonNegativeReals,
    )
    model.fleet_size = pyo.Param(
        initialize=params["fleet_size"],
        within=pyo.NonNegativeIntegers,
    )

    stop_count = len(model.C)

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(
        model.C,
        domain=pyo.Reals,
        bounds=(1, stop_count),
    )

    def stop_departure_rule(mdl, i):
        return sum(
            mdl.x[i, j] for j in mdl.V if j != i
        ) == 1

    model.stop_departure = pyo.Constraint(
        model.C, rule=stop_departure_rule
    )

    def stop_arrival_rule(mdl, j):
        return sum(
            mdl.x[i, j] for i in mdl.V if i != j
        ) == 1

    model.stop_arrival = pyo.Constraint(
        model.C, rule=stop_arrival_rule
    )

    model.depot_departure = pyo.Constraint(
        expr=sum(model.x[0, j] for j in model.C) == model.fleet_size
    )
    model.depot_arrival = pyo.Constraint(
        expr=sum(model.x[i, 0] for i in model.C) == model.fleet_size
    )

    def subtour_rule(mdl, i, j):
        return (
            mdl.u[i] - mdl.u[j] + stop_count * mdl.x[i, j]
            <= stop_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.S, rule=subtour_rule
    )

    model.total_distance = pyo.Objective(
        expr=sum(
            model.distance_matrix[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_distance))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}