# IR: {"sets":{"V":["A","B","C","D"],"E":"ordered pairs (i,j) in V x V with i != j","S":"subsets of V with 2 <= cardinality <= 3"},"params":{"cost_AB":"cost A->B","cost_AC":"cost A->C","cost_AD":"cost A->D","cost_BA":"cost B->A","cost_BC":"cost B->C","cost_BD":"cost B->D","cost_CA":"cost C->A","cost_CB":"cost C->B","cost_CD":"cost C->D","cost_DA":"cost D->A","cost_DB":"cost D->B","cost_DC":"cost D->C"},"variables":{"x[i,j]":"binary for (i,j) in E"},"constraints":["sum(x[i,j] for j != i) = 1 for each i in V","sum(x[i,j] for i != j) = 1 for each j in V","sum(x[i,j] for i,j in S with i != j) <= cardinality(S)-1 for each S"],"objective":"minimize sum(cost_ij*x[i,j] for (i,j) in E)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = ("A", "B", "C", "D")
    arcs = tuple(
        (origin, destination)
        for origin in cities
        for destination in cities
        if origin != destination
    )

    costs = {
        ("A", "B"): params["cost_AB"],
        ("A", "C"): params["cost_AC"],
        ("A", "D"): params["cost_AD"],
        ("B", "A"): params["cost_BA"],
        ("B", "C"): params["cost_BC"],
        ("B", "D"): params["cost_BD"],
        ("C", "A"): params["cost_CA"],
        ("C", "B"): params["cost_CB"],
        ("C", "D"): params["cost_CD"],
        ("D", "A"): params["cost_DA"],
        ("D", "B"): params["cost_DB"],
        ("D", "C"): params["cost_DC"],
    }

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.delivery_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(problem, origin):
        return sum(
            problem.x[origin, destination]
            for destination in cities
            if destination != origin
        ) == 1

    def incoming_rule(problem, destination):
        return sum(
            problem.x[origin, destination]
            for origin in cities
            if origin != destination
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    model.subtour_limits = pyo.ConstraintList()
    for subset_size in range(2, len(cities)):
        for subset in combinations(cities, subset_size):
            model.subtour_limits.add(
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
            model.delivery_cost[origin, destination]
            * model.x[origin, destination]
            for origin, destination in arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected solver errors remain visible to the caller.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no objective available"}

    return {"objective": obj_val, "status": "optimal"}