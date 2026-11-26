# IR: {"sets":{"locations":["E","F","G","H"],"arcs":"ordered pairs (i,j) of distinct locations","subsets":"all location subsets S with 2 <= |S| < num_locations"},"params":{"cost_EF":"E->F cost","cost_EG":"E->G cost","cost_EH":"E->H cost","cost_FE":"F->E cost","cost_FG":"F->G cost","cost_FH":"F->H cost","cost_GE":"G->E cost","cost_GF":"G->F cost","cost_GH":"G->H cost","cost_HE":"H->E cost","cost_HF":"H->F cost","cost_HG":"H->G cost","num_locations":"fixed location cardinality; must equal |locations|"},"variables":{"x[i,j]":"binary for each arc; 1 iff route uses i->j"},"constraints":["For each i: sum(x[i,j] for j != i) = 1","For each j: sum(x[i,j] for i != j) = 1","For each S in subsets: sum(x[i,j] for i,j in S with i != j) <= |S|-1"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in arcs)"}

from itertools import combinations

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    locations = ("E", "F", "G", "H")
    num_locations = params["num_locations"]

    costs = {
        ("E", "F"): params["cost_EF"],
        ("E", "G"): params["cost_EG"],
        ("E", "H"): params["cost_EH"],
        ("F", "E"): params["cost_FE"],
        ("F", "G"): params["cost_FG"],
        ("F", "H"): params["cost_FH"],
        ("G", "E"): params["cost_GE"],
        ("G", "F"): params["cost_GF"],
        ("G", "H"): params["cost_GH"],
        ("H", "E"): params["cost_HE"],
        ("H", "F"): params["cost_HF"],
        ("H", "G"): params["cost_HG"],
    }

    if num_locations != len(locations):
        return {"objective": None, "status": "invalid_num_locations"}

    arcs = [
        (origin, destination)
        for origin in locations
        for destination in locations
        if origin != destination
    ]

    model = pyo.ConcreteModel()
    model.locations = pyo.Set(initialize=locations, ordered=True)
    model.arcs = pyo.Set(dimen=2, initialize=arcs, ordered=True)
    model.delivery_cost = pyo.Param(
        model.arcs, initialize=costs, within=pyo.Reals
    )
    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def outgoing_rule(instance, origin):
        return sum(
            instance.x[origin, destination]
            for destination in instance.locations
            if destination != origin
        ) == 1

    def incoming_rule(instance, destination):
        return sum(
            instance.x[origin, destination]
            for origin in instance.locations
            if origin != destination
        ) == 1

    model.outgoing = pyo.Constraint(model.locations, rule=outgoing_rule)
    model.incoming = pyo.Constraint(model.locations, rule=incoming_rule)

    model.subtour_constraints = pyo.ConstraintList()
    for subset_size in range(2, len(locations)):
        for subset in combinations(locations, subset_size):
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
            model.delivery_cost[origin, destination]
            * model.x[origin, destination]
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