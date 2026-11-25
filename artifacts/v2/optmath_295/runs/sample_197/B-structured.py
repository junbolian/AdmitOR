# IR: {"sets":{"C":[0,1,2,3],"N":[1,2,3],"A":"{(i,j) in C x C: i != j}"},"params":["cost_0_1","cost_0_2","cost_0_3","cost_1_0","cost_1_2","cost_1_3","cost_2_0","cost_2_1","cost_2_3","cost_3_0","cost_3_1","cost_3_2","num_cities","city0_position","position_lower_bound","position_upper_bound"],"variables":{"x[i,j]":"binary, (i,j) in A","position[i]":"integer, i in C"},"constraints":["sum(x[i,j] for j in C if j != i) = 1 for i in C","sum(x[i,j] for i in C if i != j) = 1 for j in C","position[0] = city0_position","position_lower_bound <= position[i] <= position_upper_bound for i in N","position[i] - position[j] + num_cities*x[i,j] <= num_cities - 1 for distinct i,j in N"],"objective":"minimize sum(cost_i_j*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
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

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=[0, 1, 2, 3], ordered=True)
    model.nonstart_cities = pyo.Set(initialize=[1, 2, 3], ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (origin, destination)
            for origin in model.cities
            for destination in model.cities
            if origin != destination
        ],
    )

    model.travel_cost = pyo.Param(model.arcs, initialize=travel_costs)
    model.city_count = pyo.Param(initialize=params["num_cities"])
    model.start_position = pyo.Param(initialize=params["city0_position"])
    model.position_lb = pyo.Param(initialize=params["position_lower_bound"])
    model.position_ub = pyo.Param(initialize=params["position_upper_bound"])

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def position_bounds(mdl, city):
        if city == 0:
            return (None, None)
        return (
            pyo.value(mdl.position_lb),
            pyo.value(mdl.position_ub),
        )

    model.position = pyo.Var(
        model.cities,
        domain=pyo.Integers,
        bounds=position_bounds,
    )
    model.position[0].fix(pyo.value(model.start_position))

    def outgoing_rule(mdl, origin):
        return sum(
            mdl.x[origin, destination]
            for destination in mdl.cities
            if destination != origin
        ) == 1

    model.outgoing_route = pyo.Constraint(
        model.cities,
        rule=outgoing_rule,
    )

    def incoming_rule(mdl, destination):
        return sum(
            mdl.x[origin, destination]
            for origin in mdl.cities
            if origin != destination
        ) == 1

    model.incoming_route = pyo.Constraint(
        model.cities,
        rule=incoming_rule,
    )

    def subtour_rule(mdl, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            mdl.position[origin]
            - mdl.position[destination]
            + mdl.city_count * mdl.x[origin, destination]
            <= mdl.city_count - 1
        )

    # Ordering applies between nonstarting cities; the return to City 0
    # closes the tour without requiring positions to increase around a cycle.
    model.subtour_elimination = pyo.Constraint(
        model.nonstart_cities,
        model.nonstart_cities,
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
    except RuntimeError as error:
        if "a feasible solution was not found" in str(error).lower():
            return {
                "objective": None,
                "status": "infeasible_or_no_solution",
            }
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}