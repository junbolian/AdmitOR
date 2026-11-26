# IR: {"sets":{"V":["A","B","C","D","E"],"E":"{(i,j) in V x V: i != j}","S":"{S subset V: 2 <= |S| <= 4}"},"params":{"cost_AB":"real","cost_AC":"real","cost_AD":"real","cost_AE":"real","cost_BA":"real","cost_BC":"real","cost_BD":"real","cost_BE":"real","cost_CA":"real","cost_CB":"real","cost_CD":"real","cost_CE":"real","cost_DA":"real","cost_DB":"real","cost_DC":"real","cost_DE":"real","cost_EA":"real","cost_EB":"real","cost_EC":"real","cost_ED":"real"},"variables":{"x[i,j]":"binary for (i,j) in E"},"constraints":["For each i in V: sum(x[i,j] for j in V if j != i) = 1","For each j in V: sum(x[i,j] for i in V if i != j) = 1","For each S in S: sum(x[i,j] for i,j in S if i != j) <= |S| - 1"],"objective":"minimize sum(cost_ij * x[i,j] for (i,j) in E)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    warehouses = ("A", "B", "C", "D", "E")
    arcs = [
        (origin, destination)
        for origin in warehouses
        for destination in warehouses
        if origin != destination
    ]
    costs = {
        ("A", "B"): params["cost_AB"],
        ("A", "C"): params["cost_AC"],
        ("A", "D"): params["cost_AD"],
        ("A", "E"): params["cost_AE"],
        ("B", "A"): params["cost_BA"],
        ("B", "C"): params["cost_BC"],
        ("B", "D"): params["cost_BD"],
        ("B", "E"): params["cost_BE"],
        ("C", "A"): params["cost_CA"],
        ("C", "B"): params["cost_CB"],
        ("C", "D"): params["cost_CD"],
        ("C", "E"): params["cost_CE"],
        ("D", "A"): params["cost_DA"],
        ("D", "B"): params["cost_DB"],
        ("D", "C"): params["cost_DC"],
        ("D", "E"): params["cost_DE"],
        ("E", "A"): params["cost_EA"],
        ("E", "B"): params["cost_EB"],
        ("E", "C"): params["cost_EC"],
        ("E", "D"): params["cost_ED"],
    }

    model = pyo.ConcreteModel()
    model.warehouses = pyo.Set(initialize=warehouses, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.travel_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(problem, origin):
        return sum(
            problem.x[origin, destination]
            for destination in problem.warehouses
            if destination != origin
        ) == 1

    def incoming_rule(problem, destination):
        return sum(
            problem.x[origin, destination]
            for origin in problem.warehouses
            if origin != destination
        ) == 1

    model.outgoing = pyo.Constraint(model.warehouses, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.warehouses, rule=incoming_rule)

    model.subtour_constraints = pyo.ConstraintList()
    for subset_size in range(2, len(warehouses)):
        for subset in combinations(warehouses, subset_size):
            model.subtour_constraints.add(
                sum(
                    model.x[origin, destination]
                    for origin in subset
                    for destination in subset
                    if origin != destination
                )
                <= len(subset) - 1
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
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}