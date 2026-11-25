# IR: {"sets":{"R":"0..7","E":"0..8"},"params":{"d":"params['durations']","pairs":"params['conflict_pairs']","H":"sum(d[r] for r in R)"},"variables":{"start[r]":"continuous, 0 <= start[r] <= H-d[r]","before[e]":"binary","makespan":"continuous, 0 <= makespan <= H"},"constraints":["For r in R: start[r] + d[r] <= makespan","For e in E, (i,j)=pairs[e]: start[i] + d[i] <= start[j] + H*(1-before[e])","For e in E, (i,j)=pairs[e]: start[j] + d[j] <= start[i] + H*before[e]"],"objective":"minimize makespan"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    durations = params["durations"]
    conflict_pairs = params["conflict_pairs"]

    horizon = sum(durations[robot] for robot in range(8))

    model = pyo.ConcreteModel()
    model.robots = pyo.RangeSet(0, 7)
    model.edges = pyo.RangeSet(0, 8)

    model.duration = pyo.Param(
        model.robots,
        initialize=lambda mdl, robot: durations[robot],
        within=pyo.NonNegativeReals,
    )
    model.horizon = pyo.Param(
        initialize=horizon,
        within=pyo.NonNegativeReals,
    )

    def start_bounds(mdl, robot):
        return (0, horizon - durations[robot])

    model.start = pyo.Var(
        model.robots,
        domain=pyo.NonNegativeReals,
        bounds=start_bounds,
    )
    model.before = pyo.Var(model.edges, domain=pyo.Binary)
    model.makespan = pyo.Var(
        domain=pyo.NonNegativeReals,
        bounds=(0, horizon),
    )

    def completion_rule(mdl, robot):
        return mdl.start[robot] + mdl.duration[robot] <= mdl.makespan

    model.completion_limits = pyo.Constraint(
        model.robots,
        rule=completion_rule,
    )

    def forward_rule(mdl, edge):
        first, second = conflict_pairs[edge]
        return (
            mdl.start[first] + mdl.duration[first]
            <= mdl.start[second] + mdl.horizon * (1 - mdl.before[edge])
        )

    model.forward_separation = pyo.Constraint(
        model.edges,
        rule=forward_rule,
    )

    def reverse_rule(mdl, edge):
        first, second = conflict_pairs[edge]
        return (
            mdl.start[second] + mdl.duration[second]
            <= mdl.start[first] + mdl.horizon * mdl.before[edge]
        )

    model.reverse_separation = pyo.Constraint(
        model.edges,
        rule=reverse_rule,
    )

    model.total_completion = pyo.Objective(
        expr=model.makespan,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_completion))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}