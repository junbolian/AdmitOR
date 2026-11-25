# IR: {"sets":{"A":"0..6","E":"0..6"},"params":{"architect_rankings":"params['architect_rankings']; each row lists engineers from best to worst","engineer_rankings":"params['engineer_rankings']; each row lists architects from best to worst","wa":"params['friction_cost_architect_rank_weight']","we":"params['friction_cost_engineer_rank_weight']","ra[a,e]":"zero-based position of e in architect_rankings[a]","re[e,a]":"zero-based position of a in engineer_rankings[e]"},"variables":{"x[a,e]":"Binary"},"constraints":["For every a: sum(e in E, x[a,e]) = 1","For every e: sum(a in A, x[a,e]) = 1","For every (a,e): x[a,e] + sum(j in E with ra[a,j] < ra[a,e], x[a,j]) + sum(i in A with re[e,i] < re[e,a], x[i,e]) >= 1"],"objective":"Minimize sum(a in A, e in E, (wa*ra[a,e] + we*re[e,a])*x[a,e])"}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    architect_rankings = params["architect_rankings"]
    engineer_rankings = params["engineer_rankings"]
    architect_weight = params["friction_cost_architect_rank_weight"]
    engineer_weight = params["friction_cost_engineer_rank_weight"]

    participants = range(7)
    expected_candidates = set(participants)

    for label, rankings in (
        ("architect_rankings", architect_rankings),
        ("engineer_rankings", engineer_rankings),
    ):
        if len(rankings) != len(participants):
            raise ValueError(f"{label} must contain seven rows.")
        for row in rankings:
            if len(row) != len(participants) or set(row) != expected_candidates:
                raise ValueError(
                    f"Each row of {label} must be a permutation of indices 0..6."
                )

    architect_positions = {
        (architect, engineer): position
        for architect in participants
        for position, engineer in enumerate(architect_rankings[architect])
    }
    engineer_positions = {
        (engineer, architect): position
        for engineer in participants
        for position, architect in enumerate(engineer_rankings[engineer])
    }

    model = pyo.ConcreteModel()
    model.A = pyo.RangeSet(0, 6)
    model.E = pyo.RangeSet(0, 6)

    model.wa = pyo.Param(initialize=architect_weight, within=pyo.Reals)
    model.we = pyo.Param(initialize=engineer_weight, within=pyo.Reals)
    model.ra = pyo.Param(
        model.A,
        model.E,
        initialize=architect_positions,
        within=pyo.NonNegativeIntegers,
    )
    model.re = pyo.Param(
        model.E,
        model.A,
        initialize=engineer_positions,
        within=pyo.NonNegativeIntegers,
    )

    model.x = pyo.Var(model.A, model.E, domain=pyo.Binary)

    def architect_assignment_rule(instance, architect):
        return sum(
            instance.x[architect, engineer] for engineer in instance.E
        ) == 1

    def engineer_assignment_rule(instance, engineer):
        return sum(
            instance.x[architect, engineer] for architect in instance.A
        ) == 1

    def stability_rule(instance, architect, engineer):
        preferred_engineers = (
            candidate
            for candidate in instance.E
            if architect_positions[architect, candidate]
            < architect_positions[architect, engineer]
        )
        preferred_architects = (
            candidate
            for candidate in instance.A
            if engineer_positions[engineer, candidate]
            < engineer_positions[engineer, architect]
        )
        return (
            instance.x[architect, engineer]
            + sum(
                instance.x[architect, candidate]
                for candidate in preferred_engineers
            )
            + sum(
                instance.x[candidate, engineer]
                for candidate in preferred_architects
            )
            >= 1
        )

    model.architect_assignment = pyo.Constraint(
        model.A, rule=architect_assignment_rule
    )
    model.engineer_assignment = pyo.Constraint(
        model.E, rule=engineer_assignment_rule
    )
    model.stability = pyo.Constraint(
        model.A, model.E, rule=stability_rule
    )

    model.total_friction = pyo.Objective(
        expr=sum(
            (
                model.wa * model.ra[architect, engineer]
                + model.we * model.re[engineer, architect]
            )
            * model.x[architect, engineer]
            for architect in model.A
            for engineer in model.E
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except ApplicationError:
        return {"objective": None, "status": "solver_failed"}
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_friction))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}