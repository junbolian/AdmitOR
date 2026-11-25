# IR: {"sets":{"V":[0,1,2,3,4],"U":[1,2,3,4],"A":"{(i,j) in V x V: i != j}"},"params":{"cost":"params['cost'], indexed by (i,j); accepts a nested matrix/mapping or tuple-keyed mapping"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"integer in [1,4] for i in U; no position variable or constraint for city 0"},"constraints":["Departure: sum(x[i,j] for j in V if j != i) = 1 for every i in V","Arrival: sum(x[i,j] for i in V if i != j) = 1 for every j in V","MTZ: u[j] >= u[i] + 1 - 4*(1-x[i,j]) for distinct i,j in U; together with the degree constraints, this eliminates subtours and makes positions unique"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["cost"]

    def read_cost(i, j):
        if isinstance(costs, Mapping) and (i, j) in costs:
            return costs[i, j]
        return costs[i][j]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=range(5), ordered=True)
    model.non_depot = pyo.Set(initialize=range(1, 5), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(5)
            for j in range(5)
            if i != j
        ],
    )

    model.delivery_cost = pyo.Param(
        model.arcs,
        initialize=lambda model, i, j: read_cost(i, j),
        within=pyo.Reals,
    )
    model.route = pyo.Var(model.arcs, domain=pyo.Binary)
    model.position = pyo.Var(
        model.non_depot,
        domain=pyo.Integers,
        bounds=(1, 4),
    )

    def departure_rule(model, i):
        return sum(
            model.route[i, j] for j in model.cities if j != i
        ) == 1

    model.departure_constraints = pyo.Constraint(
        model.cities, rule=departure_rule
    )

    def arrival_rule(model, j):
        return sum(
            model.route[i, j] for i in model.cities if i != j
        ) == 1

    model.arrival_constraints = pyo.Constraint(
        model.cities, rule=arrival_rule
    )

    def position_rule(model, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            model.position[j]
            >= model.position[i] + 1 - 4 * (1 - model.route[i, j])
        )

    model.position_constraints = pyo.Constraint(
        model.non_depot,
        model.non_depot,
        rule=position_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.delivery_cost[i, j] * model.route[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}