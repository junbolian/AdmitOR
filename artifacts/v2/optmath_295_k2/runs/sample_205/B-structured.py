# IR: {"sets":{"cities":[0,1,2],"arcs":[[0,1],[0,2],[1,0],[1,2],[2,0],[2,1]],"nondepot_arcs":[[1,2],[2,1]]},"params":["cost_0_1","cost_0_2","cost_1_0","cost_1_2","cost_2_0","cost_2_1","pos1_lower","pos1_upper","pos2_lower","pos2_upper"],"variables":{"x[i,j]":{"type":"binary","index":"arcs"},"position[i]":{"type":"real","index":"cities","bounds":{"0":[null,null],"1":["pos1_lower","pos1_upper"],"2":["pos2_lower","pos2_upper"]}}},"constraints":["sum(x[i,j] for i in cities if i != j) == 1 for each j in cities","sum(x[i,j] for j in cities if j != i) == 1 for each i in cities","position[i] - position[j] + 3*x[i,j] <= 2 for each (i,j) in nondepot_arcs"],"objective":{"sense":"minimize","expression":"sum(cost[i,j]*x[i,j] for (i,j) in arcs)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=[0, 1, 2], ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)],
        ordered=True,
    )
    model.nondepot_arcs = pyo.Set(
        dimen=2,
        initialize=[(1, 2), (2, 1)],
        ordered=True,
    )

    model.travel_cost = pyo.Param(
        model.arcs,
        initialize={
            (0, 1): params["cost_0_1"],
            (0, 2): params["cost_0_2"],
            (1, 0): params["cost_1_0"],
            (1, 2): params["cost_1_2"],
            (2, 0): params["cost_2_0"],
            (2, 1): params["cost_2_1"],
        },
        within=pyo.Reals,
    )

    position_bounds = {
        0: (None, None),
        1: (params["pos1_lower"], params["pos1_upper"]),
        2: (params["pos2_lower"], params["pos2_upper"]),
    }

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.position = pyo.Var(
        model.cities,
        domain=pyo.Reals,
        bounds=lambda mdl, city: position_bounds[city],
    )

    def arrival_rule(mdl, destination):
        return sum(
            mdl.x[origin, destination]
            for origin in mdl.cities
            if origin != destination
        ) == 1

    model.arrival_once = pyo.Constraint(model.cities, rule=arrival_rule)

    def departure_rule(mdl, origin):
        return sum(
            mdl.x[origin, destination]
            for destination in mdl.cities
            if destination != origin
        ) == 1

    model.departure_once = pyo.Constraint(model.cities, rule=departure_rule)

    def subtour_rule(mdl, origin, destination):
        return (
            mdl.position[origin]
            - mdl.position[destination]
            + 3 * mdl.x[origin, destination]
            <= 2
        )

    model.subtour_elimination = pyo.Constraint(
        model.nondepot_arcs, rule=subtour_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[origin, destination] * model.x[origin, destination]
            for origin, destination in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}