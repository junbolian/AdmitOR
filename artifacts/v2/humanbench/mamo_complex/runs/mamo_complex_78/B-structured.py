# IR: {"sets":{"V":["A","B","C","D","E","F"],"E":"unordered pairs of distinct vertices","S":"subsets of V with 2 <= size <= 5"},"params":["cost_AB","cost_AC","cost_AD","cost_AE","cost_AF","cost_BC","cost_BD","cost_BE","cost_BF","cost_CD","cost_CE","cost_CF","cost_DE","cost_DF","cost_EF"],"variables":{"x[i,j]":"binary for (i,j) in E"},"constraints":["For each vertex v: sum(x[i,j] for incident edges (i,j)) = 2","For each subset S: sum(x[i,j] for edges internal to S) <= size(S)-1"],"objective":"minimize sum(cost_ij*x[i,j] for (i,j) in E)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    vertices = ("A", "B", "C", "D", "E", "F")
    edges = tuple(combinations(vertices, 2))

    costs = {
        ("A", "B"): params["cost_AB"],
        ("A", "C"): params["cost_AC"],
        ("A", "D"): params["cost_AD"],
        ("A", "E"): params["cost_AE"],
        ("A", "F"): params["cost_AF"],
        ("B", "C"): params["cost_BC"],
        ("B", "D"): params["cost_BD"],
        ("B", "E"): params["cost_BE"],
        ("B", "F"): params["cost_BF"],
        ("C", "D"): params["cost_CD"],
        ("C", "E"): params["cost_CE"],
        ("C", "F"): params["cost_CF"],
        ("D", "E"): params["cost_DE"],
        ("D", "F"): params["cost_DF"],
        ("E", "F"): params["cost_EF"],
    }

    model = pyo.ConcreteModel()
    model.vertices = pyo.Set(initialize=vertices, ordered=True)
    model.edges = pyo.Set(dimen=2, initialize=edges, ordered=True)
    model.delivery_cost = pyo.Param(model.edges, initialize=costs)
    model.x = pyo.Var(model.edges, domain=pyo.Binary)

    def degree_rule(block, vertex):
        return sum(
            block.x[first, second]
            for first, second in edges
            if vertex == first or vertex == second
        ) == 2

    model.degree_constraints = pyo.Constraint(
        model.vertices, rule=degree_rule
    )

    model.subtour_constraints = pyo.ConstraintList()
    for subset_size in range(2, len(vertices)):
        for subset in combinations(vertices, subset_size):
            model.subtour_constraints.add(
                sum(
                    model.x[first, second]
                    for first, second in combinations(subset, 2)
                )
                <= subset_size - 1
            )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.delivery_cost[first, second] * model.x[first, second]
            for first, second in edges
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