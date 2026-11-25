# IR: {"sets":{"Teams":[1,2,3],"groups":{"sel1_sel3":{"teams":[1,3],"events":[1,6,9,23]},"sel1_sel2":{"teams":[1,2],"events":[2,5,14,19,20]},"sel2_single":{"teams":[2],"events":[3,8,10,25,26]},"all_three":{"teams":[1,2,3],"events":[4,7,13,17,21,22,24,27]},"sel3_single":{"teams":[3],"events":[11,16,18]},"sel2_sel3":{"teams":[2,3],"events":[12]},"sel1_single":{"teams":[1],"events":[15,20]}}},"params":{"cost[t]":"cost_team1,cost_team2,cost_team3 in team order","coefficient[g,t]":"coef_<group>: scalar broadcast to group teams, or list/tuple in group team order","demand[g]":"rhs_<group> for each group"},"variables":{"Selected[t]":"Binary"},"constraints":["For each group g and each event e in groups[g].events: sum(coefficient[g,t]*Selected[t] for t in groups[g].teams) >= demand[g]; retain both constraints for event 20."],"objective":"minimize sum(cost[t]*Selected[t] for t in Teams)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    groups = {
        "sel1_sel3": {
            "teams": (1, 3),
            "events": (1, 6, 9, 23),
        },
        "sel1_sel2": {
            "teams": (1, 2),
            "events": (2, 5, 14, 19, 20),
        },
        "sel2_single": {
            "teams": (2,),
            "events": (3, 8, 10, 25, 26),
        },
        "all_three": {
            "teams": (1, 2, 3),
            "events": (4, 7, 13, 17, 21, 22, 24, 27),
        },
        "sel3_single": {
            "teams": (3,),
            "events": (11, 16, 18),
        },
        "sel2_sel3": {
            "teams": (2, 3),
            "events": (12,),
        },
        "sel1_single": {
            "teams": (1,),
            "events": (15, 20),
        },
    }

    raw_coefficients = {
        "sel1_sel3": params["coef_sel1_sel3"],
        "sel1_sel2": params["coef_sel1_sel2"],
        "sel2_single": params["coef_sel2_single"],
        "all_three": params["coef_all_three"],
        "sel3_single": params["coef_sel3_single"],
        "sel2_sel3": params["coef_sel2_sel3"],
        "sel1_single": params["coef_sel1_single"],
    }

    coefficients = {}
    for group_key, group_data in groups.items():
        teams = group_data["teams"]
        raw_value = raw_coefficients[group_key]

        if isinstance(raw_value, (list, tuple)):
            if len(raw_value) != len(teams):
                raise ValueError(
                    f"coef_{group_key} must contain {len(teams)} "
                    "coefficients in group team order."
                )
            team_coefficients = raw_value
        else:
            team_coefficients = (raw_value,) * len(teams)

        for team, coefficient in zip(teams, team_coefficients):
            coefficients[group_key, team] = coefficient

    model = pyo.ConcreteModel()

    model.Teams = pyo.Set(initialize=(1, 2, 3), ordered=True)
    model.CoverGroups = pyo.Set(initialize=tuple(groups), ordered=True)
    model.GroupTeams = pyo.Set(
        dimen=2,
        initialize=[
            (group_key, team)
            for group_key, group_data in groups.items()
            for team in group_data["teams"]
        ],
        ordered=True,
    )
    model.CoverRows = pyo.Set(
        dimen=2,
        initialize=[
            (group_key, event)
            for group_key, group_data in groups.items()
            for event in group_data["events"]
        ],
        ordered=True,
    )

    model.DeploymentCost = pyo.Param(
        model.Teams,
        within=pyo.Reals,
        initialize={
            1: params["cost_team1"],
            2: params["cost_team2"],
            3: params["cost_team3"],
        },
    )
    model.CoverCoefficient = pyo.Param(
        model.GroupTeams,
        within=pyo.Reals,
        initialize=coefficients,
    )
    model.CoverDemand = pyo.Param(
        model.CoverGroups,
        within=pyo.Reals,
        initialize={
            "sel1_sel3": params["rhs_sel1_sel3"],
            "sel1_sel2": params["rhs_sel1_sel2"],
            "sel2_single": params["rhs_sel2_single"],
            "all_three": params["rhs_all_three"],
            "sel3_single": params["rhs_sel3_single"],
            "sel2_sel3": params["rhs_sel2_sel3"],
            "sel1_single": params["rhs_sel1_single"],
        },
    )

    model.Selected = pyo.Var(model.Teams, domain=pyo.Binary)

    def coverage_rule(instance, group_key, event):
        return (
            sum(
                instance.CoverCoefficient[group_key, team]
                * instance.Selected[team]
                for team in groups[group_key]["teams"]
            )
            >= instance.CoverDemand[group_key]
        )

    model.MultiCover = pyo.Constraint(
        model.CoverRows,
        rule=coverage_rule,
    )
    model.TotalDeploymentCost = pyo.Objective(
        expr=sum(
            model.DeploymentCost[team] * model.Selected[team]
            for team in model.Teams
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
        obj_val = float(pyo.value(model.TotalDeploymentCost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}