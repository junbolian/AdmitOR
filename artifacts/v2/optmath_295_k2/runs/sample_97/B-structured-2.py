# IR: {"sets":{"A":[0,1,2,3,4],"P":"{(i,j): i,j in A, i<j}"},"params":{"earliest":"A -> real","latest":"A -> real","target":"A -> real","early_cost":"A -> nonnegative real","late_cost":"A -> nonnegative real","separation":"P -> nonnegative real","M_forward":"max(0,latest[i]+separation[i,j]-earliest[j])","M_reverse":"max(0,latest[j]+separation[i,j]-earliest[i])"},"variables":{"landing":"A -> real, bounded by earliest and latest","early":"A -> nonnegative real","late":"A -> nonnegative real","before":"P -> binary; 1 means i lands before j"},"constraints":["landing[i]-target[i]=late[i]-early[i] for i in A","landing[j]>=landing[i]+separation[i,j]-M_forward[i,j]*(1-before[i,j]) for (i,j) in P","landing[i]>=landing[j]+separation[i,j]-M_reverse[i,j]*before[i,j] for (i,j) in P"],"objective":"minimize sum(early_cost[i]*early[i]+late_cost[i]*late[i] for i in A)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the five-aircraft landing problem.

    Aircraft-indexed inputs may be sequences or mappings keyed by integer
    aircraft IDs.

    separation may be:
      * a mapping keyed by (i, j), with i < j;
      * a sequence of ten values in lexicographic pair order; or
      * a 5-by-5 nested sequence, using entries with i < j.
    """
    aircraft = tuple(range(5))
    pairs = tuple(
        (i, j)
        for i in aircraft
        for j in aircraft
        if i < j
    )

    earliest = {i: float(params["earliest"][i]) for i in aircraft}
    latest = {i: float(params["latest"][i]) for i in aircraft}
    target = {i: float(params["target"][i]) for i in aircraft}
    early_cost = {i: float(params["early_cost"][i]) for i in aircraft}
    late_cost = {i: float(params["late_cost"][i]) for i in aircraft}

    separation_input = params["separation"]
    if isinstance(separation_input, Mapping):
        separation = {
            (i, j): float(separation_input[(i, j)])
            for i, j in pairs
        }
    elif len(separation_input) == len(pairs):
        separation = {
            pair: float(separation_input[position])
            for position, pair in enumerate(pairs)
        }
    else:
        separation = {
            (i, j): float(separation_input[i][j])
            for i, j in pairs
        }

    if any(earliest[i] > latest[i] for i in aircraft):
        return {"objective": None, "status": "infeasible"}

    model = pyo.ConcreteModel()
    model.A = pyo.Set(initialize=aircraft, ordered=True)
    model.P = pyo.Set(initialize=pairs, dimen=2, ordered=True)

    model.earliest = pyo.Param(model.A, initialize=earliest)
    model.latest = pyo.Param(model.A, initialize=latest)
    model.target = pyo.Param(model.A, initialize=target)
    model.early_cost = pyo.Param(
        model.A, initialize=early_cost, within=pyo.NonNegativeReals
    )
    model.late_cost = pyo.Param(
        model.A, initialize=late_cost, within=pyo.NonNegativeReals
    )
    model.separation = pyo.Param(
        model.P, initialize=separation, within=pyo.NonNegativeReals
    )

    model.M_forward = pyo.Param(
        model.P,
        initialize={
            (i, j): max(
                0.0, latest[i] + separation[i, j] - earliest[j]
            )
            for i, j in pairs
        },
    )
    model.M_reverse = pyo.Param(
        model.P,
        initialize={
            (i, j): max(
                0.0, latest[j] + separation[i, j] - earliest[i]
            )
            for i, j in pairs
        },
    )

    model.landing = pyo.Var(
        model.A,
        domain=pyo.Reals,
        bounds=lambda problem, i: (
            problem.earliest[i], problem.latest[i]
        ),
    )
    model.early = pyo.Var(model.A, domain=pyo.NonNegativeReals)
    model.late = pyo.Var(model.A, domain=pyo.NonNegativeReals)
    model.before = pyo.Var(model.P, domain=pyo.Binary)

    def deviation_rule(problem, i):
        return (
            problem.landing[i] - problem.target[i]
            == problem.late[i] - problem.early[i]
        )

    model.deviation_balance = pyo.Constraint(
        model.A, rule=deviation_rule
    )

    def forward_rule(problem, i, j):
        return problem.landing[j] >= (
            problem.landing[i]
            + problem.separation[i, j]
            - problem.M_forward[i, j] * (1 - problem.before[i, j])
        )

    model.forward_separation = pyo.Constraint(
        model.P, rule=forward_rule
    )

    def reverse_rule(problem, i, j):
        return problem.landing[i] >= (
            problem.landing[j]
            + problem.separation[i, j]
            - problem.M_reverse[i, j] * problem.before[i, j]
        )

    model.reverse_separation = pyo.Constraint(
        model.P, rule=reverse_rule
    )

    model.total_penalty = pyo.Objective(
        expr=sum(
            model.early_cost[i] * model.early[i]
            + model.late_cost[i] * model.late[i]
            for i in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Unexpected runtime errors remain visible to the caller.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_penalty))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}