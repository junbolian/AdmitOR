# IR: {"sets":{"cities":[0,1,2,3,4],"arcs":"(i,j) in cities x cities where i != j","nondepot":[1,2,3,4]},"params":{"cost_0_1":"real","cost_0_2":"real","cost_0_3":"real","cost_0_4":"real","cost_1_0":"real","cost_1_2":"real","cost_1_3":"real","cost_1_4":"real","cost_2_0":"real","cost_2_1":"real","cost_2_3":"real","cost_2_4":"real","cost_3_0":"real","cost_3_1":"real","cost_3_2":"real","cost_3_4":"real","cost_4_0":"real","cost_4_1":"real","cost_4_2":"real","cost_4_3":"real"},"variables":{"x[i,j]":"binary for each arc","u[i]":"real for each city; u[0] unbounded; 1 <= u[i] <= 4 for nondepot cities"},"constraints":["sum(x[i,j] for j != i) = 1 for each city i","sum(x[i,j] for i != j) = 1 for each city j","u[i] - u[j] + 5*x[i,j] <= 4 for distinct nondepot cities i,j"],"objective":"minimize sum(cost_i_j*x[i,j] for each arc)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=range(5), ordered=True)
    model.nondepot = pyo.Set(initialize=range(1, 5), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(5)
            for j in range(5)
            if i != j
        ],
    )

    costs = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (0, 3): params["cost_0_3"],
        (0, 4): params["cost_0_4"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (1, 4): params["cost_1_4"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (2, 4): params["cost_2_4"],
        (3, 0): params["cost_3_0"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
        (3, 4): params["cost_3_4"],
        (4, 0): params["cost_4_0"],
        (4, 1): params["cost_4_1"],
        (4, 2): params["cost_4_2"],
        (4, 3): params["cost_4_3"],
    }
    model.delivery_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def position_bounds(mod, i):
        return (None, None) if i == 0 else (1, 4)

    model.u = pyo.Var(
        model.cities, domain=pyo.Reals, bounds=position_bounds
    )

    def departure_rule(mod, i):
        return sum(
            mod.x[i, j] for j in mod.cities if j != i
        ) == 1

    model.departure_once = pyo.Constraint(
        model.cities, rule=departure_rule
    )

    def arrival_rule(mod, j):
        return sum(
            mod.x[i, j] for i in mod.cities if i != j
        ) == 1

    model.arrival_once = pyo.Constraint(
        model.cities, rule=arrival_rule
    )

    def subtour_rule(mod, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return mod.u[i] - mod.u[j] + 5 * mod.x[i, j] <= 4

    model.subtour_elimination = pyo.Constraint(
        model.nondepot, model.nondepot, rule=subtour_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.delivery_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        message = str(exc).lower()
        if (
            "feasible solution was not found" in message
            or "no feasible solution" in message
        ):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}