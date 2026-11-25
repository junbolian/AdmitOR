# IR: {"sets":{"cities":[0,1,2],"arcs":"(i,j) in cities x cities with i != j","position_cities":[1,2]},"params":{"cost_0_1":"arc cost (0,1)","cost_0_2":"arc cost (0,2)","cost_1_0":"arc cost (1,0)","cost_1_2":"arc cost (1,2)","cost_2_0":"arc cost (2,0)","cost_2_1":"arc cost (2,1)"},"variables":{"x[i,j]":"binary for each arc","u[i]":"continuous in [0,2] for position_cities"},"constraints":["sum(x[i,j] for j != i) = 1 for each city i","sum(x[i,j] for i != j) = 1 for each city j","u[i] - u[j] + 3*x[i,j] <= 2 for distinct i,j in position_cities"],"objective":"minimize sum(cost[i,j]*x[i,j] for each arc)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = (0, 1, 2)
    arcs = tuple((i, j) for i in cities for j in cities if i != j)
    costs = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(initialize=arcs, dimen=2, ordered=True)
    model.position_cities = pyo.Set(initialize=(1, 2), ordered=True)
    model.cost = pyo.Param(model.arcs, initialize=costs)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(
        model.position_cities, domain=pyo.Reals, bounds=(0, 2)
    )

    def outgoing_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.cities if j != i
        ) == 1

    def incoming_rule(instance, j):
        return sum(
            instance.x[i, j] for i in instance.cities if i != j
        ) == 1

    def subtour_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return instance.u[i] - instance.u[j] + 3 * instance.x[i, j] <= 2

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)
    model.subtour = pyo.Constraint(
        model.position_cities, model.position_cities, rule=subtour_rule
    )
    model.total_cost = pyo.Objective(
        expr=sum(model.cost[i, j] * model.x[i, j] for i, j in model.arcs),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}