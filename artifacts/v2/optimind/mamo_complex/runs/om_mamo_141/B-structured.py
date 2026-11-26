# IR: {"sets":{"V":["A","B","C","D","E","F"],"E":"{(i,j) in V x V: i != j}","U":"V minus {A}"},"params":{"cost[i,j]":"params['cost_'+i+j] for (i,j) in E","n":"params['num_locations']; require n == |V|"},"variables":{"x[i,j]":"binary for (i,j) in E","u[i]":"continuous in [1,n-1] for i in U"},"constraints":["For each i in V: sum(x[i,j] for j in V if j != i) == 1","For each j in V: sum(x[i,j] for i in V if i != j) == 1","For distinct i,j in U: u[i] - u[j] + n*x[i,j] <= n-1"],"objective":"Minimize sum(cost[i,j]*x[i,j] for (i,j) in E)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    locations = ("A", "B", "C", "D", "E", "F")
    num_locations = params["num_locations"]

    if num_locations != len(locations):
        return {"objective": None, "status": "invalid_num_locations"}

    arcs = tuple(
        (origin, destination)
        for origin in locations
        for destination in locations
        if origin != destination
    )
    nonroot_locations = locations[1:]

    costs = {
        (origin, destination): params[f"cost_{origin}{destination}"]
        for origin, destination in arcs
    }

    model = pyo.ConcreteModel()

    model.locations = pyo.Set(initialize=locations, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.nonroot_locations = pyo.Set(
        initialize=nonroot_locations, ordered=True
    )

    model.location_count = pyo.Param(
        initialize=num_locations, within=pyo.PositiveIntegers
    )
    model.travel_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )

    model.route_arc = pyo.Var(model.arcs, domain=pyo.Binary)
    model.visit_order = pyo.Var(
        model.nonroot_locations,
        domain=pyo.Reals,
        bounds=(1, num_locations - 1),
    )

    def outgoing_rule(instance, origin):
        return sum(
            instance.route_arc[origin, destination]
            for destination in instance.locations
            if destination != origin
        ) == 1

    model.outgoing_degree = pyo.Constraint(
        model.locations, rule=outgoing_rule
    )

    def incoming_rule(instance, destination):
        return sum(
            instance.route_arc[origin, destination]
            for origin in instance.locations
            if origin != destination
        ) == 1

    model.incoming_degree = pyo.Constraint(
        model.locations, rule=incoming_rule
    )

    def subtour_rule(instance, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            instance.visit_order[origin]
            - instance.visit_order[destination]
            + instance.location_count
            * instance.route_arc[origin, destination]
            <= instance.location_count - 1
        )

    model.subtour_elimination = pyo.Constraint(
        model.nonroot_locations,
        model.nonroot_locations,
        rule=subtour_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.route_arc[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}