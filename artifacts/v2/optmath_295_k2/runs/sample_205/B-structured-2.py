# IR: {"sets":{"cities":[0,1,2],"arcs":[[0,1],[0,2],[1,0],[1,2],[2,0],[2,1]],"ordered_non_depot_pairs":[[1,2],[2,1]]},"params":["cost_0_1","cost_0_2","cost_1_0","cost_1_2","cost_2_0","cost_2_1","pos1_lower","pos1_upper","pos2_lower","pos2_upper"],"variables":{"x[i,j]":"binary for each arc","position[0]":"unrestricted real","position[1]":"real in [pos1_lower,pos1_upper]","position[2]":"real in [pos2_lower,pos2_upper]"},"constraints":["sum(x[i,j] for i != j) = 1 for each destination j","sum(x[i,j] for j != i) = 1 for each origin i","position[i]-position[j]+1 <= max(0,upper[i]-lower[j]+1)*(1-x[i,j]) for (i,j) in ordered_non_depot_pairs"],"objective":"minimize sum(cost[i,j]*x[i,j] for each arc)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = (0, 1, 2)
    arcs = ((0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1))
    ordered_pairs = ((1, 2), (2, 1))

    costs = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
    }
    lower = {
        1: params["pos1_lower"],
        2: params["pos2_lower"],
    }
    upper = {
        1: params["pos1_upper"],
        2: params["pos2_upper"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.ordered_pairs = pyo.Set(
        initialize=ordered_pairs, dimen=2, ordered=True
    )
    model.travel_cost = pyo.Param(model.arcs, initialize=costs)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def position_bounds_rule(instance, city):
        if city == 0:
            return (None, None)
        return (lower[city], upper[city])

    model.position = pyo.Var(
        model.cities,
        domain=pyo.Reals,
        bounds=position_bounds_rule,
    )

    def arrival_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in instance.cities
            if origin != destination
        ) == 1

    model.arrival_once = pyo.Constraint(
        model.cities, rule=arrival_rule
    )

    def departure_rule(instance, origin):
        return sum(
            instance.x[origin, destination]
            for destination in instance.cities
            if destination != origin
        ) == 1

    model.departure_once = pyo.Constraint(
        model.cities, rule=departure_rule
    )

    def subtour_rule(instance, origin, destination):
        big_m = max(0, upper[origin] - lower[destination] + 1)
        return (
            instance.position[origin] - instance.position[destination] + 1
            <= big_m * (1 - instance.x[origin, destination])
        )

    model.subtour_elimination = pyo.Constraint(
        model.ordered_pairs, rule=subtour_rule
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
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}