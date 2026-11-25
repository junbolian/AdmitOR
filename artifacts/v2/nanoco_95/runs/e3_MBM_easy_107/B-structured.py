# IR: {"sets":{"U":[0,1,2,3,4,5,6],"F":[0,1,2,3,4],"E":[[0,0],[0,2],[0,3],[1,4],[2,0],[2,1],[2,2],[3,0],[3,2],[3,4],[4,0],[4,2],[4,3],[4,4],[5,0]]},"params":{},"variables":{"x[u,f]":{"index":"(u,f) in E","type":"binary"}},"constraints":["sum(x[u,f] for f with (u,f) in E) <= 1 for each u in U","sum(x[u,f] for u with (u,f) in E) <= 1 for each f in F"],"objective":{"sense":"maximize","expression":"sum(x[u,f] for (u,f) in E)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # No numerical parameters are specified; params is intentionally unused.
    model = pyo.ConcreteModel()

    model.users = pyo.Set(initialize=range(7), ordered=True)
    model.frequencies = pyo.Set(initialize=range(5), ordered=True)
    model.feasible_edges = pyo.Set(
        dimen=2,
        initialize=[
            (0, 0), (0, 2), (0, 3),
            (1, 4),
            (2, 0), (2, 1), (2, 2),
            (3, 0), (3, 2), (3, 4),
            (4, 0), (4, 2), (4, 3), (4, 4),
            (5, 0),
        ],
        ordered=True,
    )

    model.assignment = pyo.Var(model.feasible_edges, domain=pyo.Binary)

    def user_limit_rule(block, user):
        expression = pyo.quicksum(
            block.assignment[user, frequency]
            for frequency in block.frequencies
            if (user, frequency) in block.feasible_edges
        )
        # Tuple form also handles user 6's empty sum without a Boolean.
        return (None, expression, 1)

    def frequency_limit_rule(block, frequency):
        return (
            None,
            pyo.quicksum(
                block.assignment[user, frequency]
                for user in block.users
                if (user, frequency) in block.feasible_edges
            ),
            1,
        )

    model.user_limits = pyo.Constraint(
        model.users, rule=user_limit_rule
    )
    model.frequency_limits = pyo.Constraint(
        model.frequencies, rule=frequency_limit_rule
    )
    model.total_assignments = pyo.Objective(
        expr=pyo.quicksum(
            model.assignment[user, frequency]
            for user, frequency in model.feasible_edges
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}