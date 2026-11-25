# IR: {"sets":{"teams":[0,1,2,3,4],"sites":[0,1,2,3,4]},"params":{"cost_matrix":"nonnegative duration[team][site] from params"},"variables":{"assign[team,site]":"Binary","max_duration":"NonNegativeReals"},"constraints":["For each team: sum_site assign[team,site] = 1","For each site: sum_team assign[team,site] = 1","For each team: sum_site cost_matrix[team][site]*assign[team,site] <= max_duration"],"objective":"minimize max_duration"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_matrix = params["cost_matrix"]

    model = pyo.ConcreteModel()
    model.teams = pyo.RangeSet(0, 4)
    model.sites = pyo.RangeSet(0, 4)

    model.duration = pyo.Param(
        model.teams,
        model.sites,
        initialize={
            (team, site): cost_matrix[team][site]
            for team in model.teams
            for site in model.sites
        },
        within=pyo.NonNegativeReals,
    )

    model.assign = pyo.Var(model.teams, model.sites, domain=pyo.Binary)
    model.max_duration = pyo.Var(domain=pyo.NonNegativeReals)

    def team_assignment_rule(instance, team):
        return sum(
            instance.assign[team, site] for site in instance.sites
        ) == 1

    model.team_assignment = pyo.Constraint(
        model.teams, rule=team_assignment_rule
    )

    def site_assignment_rule(instance, site):
        return sum(
            instance.assign[team, site] for team in instance.teams
        ) == 1

    model.site_assignment = pyo.Constraint(
        model.sites, rule=site_assignment_rule
    )

    def duration_limit_rule(instance, team):
        return sum(
            instance.duration[team, site] * instance.assign[team, site]
            for site in instance.sites
        ) <= instance.max_duration

    model.duration_limit = pyo.Constraint(
        model.teams, rule=duration_limit_rule
    )

    model.objective = pyo.Objective(
        expr=model.max_duration,
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}