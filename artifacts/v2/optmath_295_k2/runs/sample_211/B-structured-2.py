# IR: {"sets":{"C":[0,1,2,3,4],"D":[1,2,3,4],"A":"{(i,j) in C x C: i != j}"},"params":{"cost":"cost[i,j] = params['cost_i_j'] for every (i,j) in A"},"variables":{"x[i,j]":"binary for (i,j) in A","position[i]":"integer in [0,4] for i in C"},"constraints":["sum(x[i,j] for j in C if j != i) = 1 for i in C","sum(x[i,j] for i in C if i != j) = 1 for j in C","position[0] = 0","position[i] >= 1 for i in D","position[i] - position[j] + 5*x[i,j] <= 4 for distinct i,j in D"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = tuple(range(5))
    nondepot_cities = cities[1:]
    arcs = tuple((i, j) for i in cities for j in cities if i != j)

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
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.nondepot_cities = pyo.Set(
        initialize=nondepot_cities, ordered=True
    )
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.position = pyo.Var(
        model.cities, domain=pyo.Integers, bounds=(0, 4)
    )

    def departure_rule(instance, i):
        return sum(
            instance.x[i, j] for j in cities if j != i
        ) == 1

    model.departure_constraints = pyo.Constraint(
        model.cities, rule=departure_rule
    )

    def arrival_rule(instance, j):
        return sum(
            instance.x[i, j] for i in cities if i != j
        ) == 1

    model.arrival_constraints = pyo.Constraint(
        model.cities, rule=arrival_rule
    )

    model.depot_position_constraint = pyo.Constraint(
        expr=model.position[0] == 0
    )

    def positive_position_rule(instance, i):
        return instance.position[i] >= 1

    model.positive_position_constraints = pyo.Constraint(
        model.nondepot_cities, rule=positive_position_rule
    )

    def subtour_rule(instance, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return (
            instance.position[i]
            - instance.position[j]
            + 5 * instance.x[i, j]
            <= 4
        )

    model.subtour_constraints = pyo.Constraint(
        model.nondepot_cities,
        model.nondepot_cities,
        rule=subtour_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j] for i, j in arcs
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