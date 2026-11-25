# IR: {"sets":{"users":[0,1,2,3,4,5,6],"frequencies":[0,1,2,3,4],"edges":[[0,0],[0,2],[0,3],[1,4],[2,0],[2,1],[2,2],[3,0],[3,2],[3,4],[4,0],[4,2],[4,3],[4,4],[5,0]]},"params":{},"variables":{"assigned[u,f]":{"domain":"Binary","index":"edges"}},"constraints":["For each user u: sum(assigned[u,f] for feasible edges incident to u) <= 1.","For each frequency f: sum(assigned[u,f] for feasible edges incident to f) <= 1."],"objective":"Maximize sum(assigned[u,f] for (u,f) in edges)."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Return the maximum number of feasible concurrent assignments."""
    model = pyo.ConcreteModel()

    model.users = pyo.RangeSet(0, 6)
    model.frequencies = pyo.RangeSet(0, 4)
    model.edges = pyo.Set(
        dimen=2,
        initialize=[
            (0, 0), (0, 2), (0, 3),
            (1, 4),
            (2, 0), (2, 1), (2, 2),
            (3, 0), (3, 2), (3, 4),
            (4, 0), (4, 2), (4, 3), (4, 4),
            (5, 0),
        ],
    )

    model.assigned = pyo.Var(model.edges, domain=pyo.Binary)

    def user_capacity_rule(instance, user):
        # A tuple also represents the empty sum for user 6 correctly.
        return (
            None,
            pyo.quicksum(
                instance.assigned[user, frequency]
                for frequency in instance.frequencies
                if (user, frequency) in instance.edges
            ),
            1,
        )

    def frequency_capacity_rule(instance, frequency):
        return (
            None,
            pyo.quicksum(
                instance.assigned[user, frequency]
                for user in instance.users
                if (user, frequency) in instance.edges
            ),
            1,
        )

    model.user_capacity = pyo.Constraint(
        model.users, rule=user_capacity_rule
    )
    model.frequency_capacity = pyo.Constraint(
        model.frequencies, rule=frequency_capacity_rule
    )

    model.total_assignments = pyo.Objective(
        expr=pyo.quicksum(
            model.assigned[user, frequency]
            for user, frequency in model.edges
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}