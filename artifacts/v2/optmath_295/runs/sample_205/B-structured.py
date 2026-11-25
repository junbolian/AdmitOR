# IR: {"sets":{"cities":[0,1,2],"arcs":[[0,1],[0,2],[1,0],[1,2],[2,0],[2,1]],"position_arcs":[[1,2],[2,1]]},"params":["cost_0_1","cost_0_2","cost_1_0","cost_1_2","cost_2_0","cost_2_1","position_lb_city1","position_ub_city1","position_lb_city2","position_ub_city2"],"derived":{"M[i,j]":"max(0,position_ub_city_i-position_lb_city_j+1)"},"variables":{"route[i,j]":"binary for arcs","position[0]":"unrestricted real","position[1]":"real in [position_lb_city1,position_ub_city1]","position[2]":"real in [position_lb_city2,position_ub_city2]"},"constraints":["sum(route[i,j] for j != i)=1 for each city i","sum(route[i,j] for i != j)=1 for each city j","position[i]+1<=position[j]+M[i,j]*(1-route[i,j]) for each position_arc (i,j)"],"objective":"minimize sum(cost[i,j]*route[i,j] for all arcs)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
    }
    lower_bounds = {
        1: params["position_lb_city1"],
        2: params["position_lb_city2"],
    }
    upper_bounds = {
        1: params["position_ub_city1"],
        2: params["position_ub_city2"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=list(costs), ordered=True)
    model.position_arcs = pyo.Set(
        dimen=2, initialize=[(1, 2), (2, 1)], ordered=True
    )

    model.travel_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.subtour_big_m = pyo.Param(
        model.position_arcs,
        initialize={
            (origin, destination): max(
                0,
                upper_bounds[origin] - lower_bounds[destination] + 1,
            )
            for origin, destination in [(1, 2), (2, 1)]
        },
        within=pyo.NonNegativeReals,
    )

    model.route = pyo.Var(model.arcs, domain=pyo.Binary)

    def position_bounds(instance, city):
        if city == 0:
            return None, None
        return lower_bounds[city], upper_bounds[city]

    model.position = pyo.Var(
        model.cities, domain=pyo.Reals, bounds=position_bounds
    )

    def departure_rule(instance, origin):
        return sum(
            instance.route[origin, destination]
            for destination in instance.cities
            if destination != origin
        ) == 1

    model.departure_once = pyo.Constraint(
        model.cities, rule=departure_rule
    )

    def arrival_rule(instance, destination):
        return sum(
            instance.route[origin, destination]
            for origin in instance.cities
            if origin != destination
        ) == 1

    model.arrival_once = pyo.Constraint(
        model.cities, rule=arrival_rule
    )

    def subtour_rule(instance, origin, destination):
        return (
            instance.position[origin] + 1
            <= instance.position[destination]
            + instance.subtour_big_m[origin, destination]
            * (1 - instance.route[origin, destination])
        )

    model.subtour_elimination = pyo.Constraint(
        model.position_arcs, rule=subtour_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination]
            * model.route[origin, destination]
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