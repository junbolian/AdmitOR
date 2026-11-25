# IR: {"sets":{"C":"range(num_cities)","A":"{(i,j) in C x C: i != j}","N":"C excluding 0"},"params":["cost_0_1","cost_0_2","cost_0_3","cost_1_0","cost_1_2","cost_1_3","cost_2_0","cost_2_1","cost_2_3","cost_3_0","cost_3_1","cost_3_2","num_cities","num_route_vars","position_upper_bound","city0_position_fixed"],"validation":["num_cities == 4","num_route_vars == |A|"],"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"integer in [0, position_upper_bound] for i in C"},"constraints":["u[0] = city0_position_fixed","sum(x[i,j] for j in C if j != i) = 1 for i in C","sum(x[i,j] for i in C if i != j) = 1 for j in C","num_cities*x[i,j] + u[i] - u[j] <= position_upper_bound for distinct i,j in N"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = params["num_cities"]
    num_route_vars = params["num_route_vars"]
    position_upper_bound = params["position_upper_bound"]
    city0_position_fixed = params["city0_position_fixed"]

    travel_costs = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (0, 3): params["cost_0_3"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (3, 0): params["cost_3_0"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
    }

    if num_cities != 4:
        return {"objective": None, "status": "invalid_index_sizes"}

    cities = tuple(range(num_cities))
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )

    if num_route_vars != len(arcs):
        return {"objective": None, "status": "invalid_index_sizes"}

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.nonzero_cities = pyo.Set(
        initialize=[city for city in cities if city != 0],
        ordered=True,
    )

    model.travel_cost = pyo.Param(
        model.arcs, initialize=travel_costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.cities,
        domain=pyo.Integers,
        bounds=(0, position_upper_bound),
    )

    model.start_position = pyo.Constraint(
        expr=model.u[0] == city0_position_fixed
    )

    def outgoing_rule(instance, origin):
        return sum(
            instance.x[origin, destination]
            for destination in instance.cities
            if destination != origin
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)

    def incoming_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in instance.cities
            if origin != destination
        ) == 1

    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    def subtour_rule(instance, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            num_cities * instance.x[origin, destination]
            + instance.u[origin]
            - instance.u[destination]
            <= position_upper_bound
        )

    model.subtour_elimination = pyo.Constraint(
        model.nonzero_cities,
        model.nonzero_cities,
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
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}