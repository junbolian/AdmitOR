# IR: {"sets":{"V":[0,1,2,3,4],"P":[1,2,3,4],"A":"{(i,j) in V x V: i != j}"},"params":{"cost":"cost[i,j] = params['cost_i_j'] for (i,j) in A","u_lower":"params['u_lower']","u_upper":"params['u_upper']"},"variables":{"x[i,j]":"Binary for (i,j) in A","u[i]":"Real for i in V; u[0] unbounded; u_lower <= u[i] <= u_upper for i in P"},"constraints":["sum(x[i,j] for j in V if j != i) = 1 for i in V","sum(x[i,j] for i in V if i != j) = 1 for j in V","u[i] - u[j] + 5*x[i,j] <= 4 for i,j in P with i != j"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
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

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=range(5), ordered=True)
    model.P = pyo.Set(initialize=range(1, 5), ordered=True)
    model.A = pyo.Set(dimen=2, initialize=costs.keys(), ordered=True)

    model.cost = pyo.Param(model.A, initialize=costs, within=pyo.Reals)
    model.u_lower = pyo.Param(
        initialize=params["u_lower"], within=pyo.Reals
    )
    model.u_upper = pyo.Param(
        initialize=params["u_upper"], within=pyo.Reals
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def position_bounds(mdl, city):
        if city == 0:
            return None, None
        return mdl.u_lower, mdl.u_upper

    model.u = pyo.Var(
        model.V, domain=pyo.Reals, bounds=position_bounds
    )

    def departure_rule(mdl, origin):
        return sum(
            mdl.x[origin, destination]
            for destination in mdl.V
            if destination != origin
        ) == 1

    model.departure = pyo.Constraint(model.V, rule=departure_rule)

    def arrival_rule(mdl, destination):
        return sum(
            mdl.x[origin, destination]
            for origin in mdl.V
            if origin != destination
        ) == 1

    model.arrival = pyo.Constraint(model.V, rule=arrival_rule)

    def subtour_rule(mdl, origin, destination):
        if origin == destination:
            return pyo.Constraint.Skip
        return (
            mdl.u[origin]
            - mdl.u[destination]
            + 5 * mdl.x[origin, destination]
            <= 4
        )

    model.subtour = pyo.Constraint(
        model.P, model.P, rule=subtour_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this error when it cannot load a feasible solution.
        if "feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}