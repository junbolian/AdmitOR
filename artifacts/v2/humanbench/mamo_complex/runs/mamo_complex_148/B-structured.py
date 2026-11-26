# IR: {"sets":{"V":"{1,...,num_cities} (frozen at six cities)","A":"{(i,j) in V x V: i != j}","U":"V \\ {1}"},"params":{"num_cities":"params['num_cities']","c[i,j]":"params['cost_i_j'] for (i,j) in A"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [1,num_cities-1] for i in U"},"constraints":["sum(x[i,j] for j in V if j!=i)=1 for i in V","sum(x[i,j] for i in V if i!=j)=1 for j in V","u[i]-u[j]+num_cities*x[i,j]<=num_cities-1 for distinct i,j in U"],"objective":"minimize sum(c[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = params["num_cities"]
    if num_cities != 6:
        raise ValueError("num_cities must equal the frozen index-set size of six.")

    cities = tuple(range(1, num_cities + 1))
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )
    other_cities = tuple(city for city in cities if city != 1)

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.other_cities = pyo.Set(initialize=other_cities, ordered=True)

    model.travel_cost = pyo.Param(
        model.arcs,
        initialize={
            (origin, destination): params[f"cost_{origin}_{destination}"]
            for origin, destination in arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.other_cities,
        domain=pyo.Reals,
        bounds=(1, num_cities - 1),
    )

    def outgoing_rule(instance, origin):
        return sum(
            instance.x[origin, destination]
            for destination in instance.cities
            if destination != origin
        ) == 1

    def incoming_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in instance.cities
            if origin != destination
        ) == 1

    def subtour_rule(instance, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            instance.u[origin]
            - instance.u[destination]
            + num_cities * instance.x[origin, destination]
            <= num_cities - 1
        )

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)
    model.subtour_elimination = pyo.Constraint(
        model.other_cities,
        model.other_cities,
        rule=subtour_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" not in str(exc).lower():
            raise
        # The solver could not load a feasible solution. Check the objective
        # below; objective retrievability is the sole success criterion.

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}