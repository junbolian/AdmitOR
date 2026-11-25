# IR: {"sets":{"teams":[1,2,3],"groups":{"sel1_sel3":{"rows":["e1","e6","e9","e23"],"teams":[1,3]},"sel1_sel2":{"rows":["e2","e5","e14","e19","e20"],"teams":[1,2]},"sel2_single":{"rows":["e3","e8","e10","e25","e26"],"teams":[2]},"all_three":{"rows":["e4","e7","e13","e17","e21","e22","e24","e27"],"teams":[1,2,3]},"sel3_single":{"rows":["e11","e16","e18"],"teams":[3]},"sel2_sel3":{"rows":["e12"],"teams":[2,3]},"sel1_single":{"rows":["e15","e20_single"],"teams":[1]}}},"params":{"costs":["cost_team1","cost_team2","cost_team3"],"coefficients":["coef_sel1_sel3","coef_sel1_sel2","coef_sel2_single","coef_all_three","coef_sel3_single","coef_sel2_sel3","coef_sel1_single"],"demands":["rhs_sel1_sel3","rhs_sel1_sel2","rhs_sel2_single","rhs_all_three","rhs_sel3_single","rhs_sel2_sel3","rhs_sel1_single"],"coefficient_interpretation":"A scalar applies to every team in its group; a list or tuple supplies coefficients in the group's team order. A singleton list or tuple is broadcast."},"variables":{"Selected[teams]":"binary"},"constraints":["For each group g and row r in g.rows: sum(coefficient[g,t]*Selected[t] for t in g.teams) >= demand[g].","e20_single is the additional single-team constraint also labeled e20; both e20 constraints are enforced."],"objective":"minimize sum(cost[t]*Selected[t] for t in teams)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = {
        1: params["cost_team1"],
        2: params["cost_team2"],
        3: params["cost_team3"],
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

    demands = {
        "sel1_sel3": params["rhs_sel1_sel3"],
        "sel1_sel2": params["rhs_sel1_sel2"],
        "sel2_single": params["rhs_sel2_single"],
        "all_three": params["rhs_all_three"],
        "sel3_single": params["rhs_sel3_single"],
        "sel2_sel3": params["rhs_sel2_sel3"],
        "sel1_single": params["rhs_sel1_single"],
    }

    groups = {
        "sel1_sel3": (("e1", "e6", "e9", "e23"), (1, 3)),
        "sel1_sel2": (("e2", "e5", "e14", "e19", "e20"), (1, 2)),
        "sel2_single": (("e3", "e8", "e10", "e25", "e26"), (2,)),
        "all_three": (
            ("e4", "e7", "e13", "e17", "e21", "e22", "e24", "e27"),
            (1, 2, 3),
        ),
        "sel3_single": (("e11", "e16", "e18"), (3,)),
        "sel2_sel3": (("e12",), (2, 3)),
        "sel1_single": (("e15", "e20_single"), (1,)),
    }

    coefficient_values = {}
    row_definitions = {}

    for group_name, (row_labels, team_ids) in groups.items():
        raw_value = raw_coefficients[group_name]

        if isinstance(raw_value, (list, tuple)):
            if len(raw_value) == 1:
                values = tuple(raw_value) * len(team_ids)
            elif len(raw_value) == len(team_ids):
                values = tuple(raw_value)
            else:
                raise ValueError(
                    f"coef_{group_name} must be a scalar, a singleton "
                    f"sequence, or a sequence of length {len(team_ids)}."
                )
        else:
            values = (raw_value,) * len(team_ids)

        for team_id, coefficient in zip(team_ids, values):
            coefficient_values[group_name, team_id] = coefficient

        for row_label in row_labels:
            row_definitions[row_label] = (group_name, team_ids)

    model = pyo.ConcreteModel()

    model.Teams = pyo.Set(initialize=(1, 2, 3), ordered=True)
    model.CoverageGroups = pyo.Set(
        initialize=groups.keys(), ordered=True
    )
    model.CoefficientKeys = pyo.Set(
        dimen=2, initialize=coefficient_values.keys(), ordered=True
    )
    model.CoverageRows = pyo.Set(
        initialize=row_definitions.keys(), ordered=True
    )

    model.DeploymentCost = pyo.Param(
        model.Teams, initialize=costs, within=pyo.Reals
    )
    model.CoverageCoefficient = pyo.Param(
        model.CoefficientKeys,
        initialize=coefficient_values,
        within=pyo.Reals,
    )
    model.CoverageDemand = pyo.Param(
        model.CoverageGroups, initialize=demands, within=pyo.Reals
    )

    model.Selected = pyo.Var(model.Teams, domain=pyo.Binary)

    def coverage_rule(problem, row_label):
        group_name, team_ids = row_definitions[row_label]
        return (
            sum(
                problem.CoverageCoefficient[group_name, team_id]
                * problem.Selected[team_id]
                for team_id in team_ids
            )
            >= problem.CoverageDemand[group_name]
        )

    model.MultiCover = pyo.Constraint(
        model.CoverageRows, rule=coverage_rule
    )

    model.TotalCost = pyo.Objective(
        expr=sum(
            model.DeploymentCost[team_id] * model.Selected[team_id]
            for team_id in model.Teams
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        message = str(exc).lower()
        if (
            "a feasible solution was not found" in message
            or "no feasible solution" in message
        ):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.TotalCost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}