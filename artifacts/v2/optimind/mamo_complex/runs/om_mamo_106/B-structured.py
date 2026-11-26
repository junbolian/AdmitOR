# IR: {"sets":{"V":["E","F","G","H","I"],"A":"{(i,j) in V x V: i != j}","U":"V excluding E"},"params":{"cost[i,j]":"params['cost_'+i+'_'+j] for every (i,j) in A"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [1, |V|-1] for i in U"},"constraints":["For each i in V: sum(x[i,j] for j != i) = 1","For each j in V: sum(x[i,j] for i != j) = 1","For distinct i,j in U: u[i] - u[j] + |V|*x[i,j] <= |V|-1"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ("E", "F", "G", "H", "I")
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )
    nonroot_cities = tuple(city for city in cities if city != "E")
    city_count = len(cities)

    costs = {
        ("E", "F"): params["cost_E_F"],
        ("E", "G"): params["cost_E_G"],
        ("E", "H"): params["cost_E_H"],
        ("E", "I"): params["cost_E_I"],
        ("F", "E"): params["cost_F_E"],
        ("F", "G"): params["cost_F_G"],
        ("F", "H"): params["cost_F_H"],
        ("F", "I"): params["cost_F_I"],
        ("G", "E"): params["cost_G_E"],
        ("G", "F"): params["cost_G_F"],
        ("G", "H"): params["cost_G_H"],
        ("G", "I"): params["cost_G_I"],
        ("H", "E"): params["cost_H_E"],
        ("H", "F"): params["cost_H_F"],
        ("H", "G"): params["cost_H_G"],
        ("H", "I"): params["cost_H_I"],
        ("I", "E"): params["cost_I_E"],
        ("I", "F"): params["cost_I_F"],
        ("I", "G"): params["cost_I_G"],
        ("I", "H"): params["cost_I_H"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.nonroot_cities = pyo.Set(
        initialize=nonroot_cities, ordered=True
    )
    model.cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.nonroot_cities,
        domain=pyo.Reals,
        bounds=(1, city_count - 1),
    )

    def outgoing_rule(problem, origin):
        return sum(
            problem.x[origin, destination]
            for destination in problem.cities
            if destination != origin
        ) == 1

    model.outgoing = pyo.Constraint(
        model.cities, rule=outgoing_rule
    )

    def incoming_rule(problem, destination):
        return sum(
            problem.x[origin, destination]
            for origin in problem.cities
            if origin != destination
        ) == 1

    model.incoming = pyo.Constraint(
        model.cities, rule=incoming_rule
    )

    # E is an ordering anchor; every Hamiltonian cycle includes E.
    def subtour_rule(problem, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            problem.u[origin]
            - problem.u[destination]
            + city_count * problem.x[origin, destination]
            <= city_count - 1
        )

    model.subtour = pyo.Constraint(
        model.nonroot_cities,
        model.nonroot_cities,
        rule=subtour_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}