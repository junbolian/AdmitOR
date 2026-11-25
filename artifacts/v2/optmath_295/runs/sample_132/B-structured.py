# IR: {"sets":{"Teams":[1,2,3],"E13":[1,6,9,23],"E12":[2,5,14,19,20],"E2":[3,8,10,25,26],"E123":[4,7,13,17,21,22,24,27],"E3":[11,16,18],"E23":[12],"E1":[15,20]},"params":["cost_team1","cost_team2","cost_team3","rhs_1_3","rhs_1_2","rhs_2_only","rhs_1_2_3","rhs_3_only","rhs_2_3","rhs_1_only"],"variables":{"Selected[t in Teams]":"Binary"},"constraints":["MultiCover_1_3[e in E13]: Selected[1]+Selected[3]>=rhs_1_3","MultiCover_1_2[e in E12]: Selected[1]+Selected[2]>=rhs_1_2","MultiCover_2_only[e in E2]: Selected[2]>=rhs_2_only","MultiCover_1_2_3[e in E123]: Selected[1]+Selected[2]+Selected[3]>=rhs_1_2_3","MultiCover_3_only[e in E3]: Selected[3]>=rhs_3_only","MultiCover_2_3[e in E23]: Selected[2]+Selected[3]>=rhs_2_3","MultiCover_1_only[e in E1]: Selected[1]>=rhs_1_only"],"objective":"minimize cost_team1*Selected[1]+cost_team2*Selected[2]+cost_team3*Selected[3]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.Teams = pyo.Set(initialize=[1, 2, 3], ordered=True)
    model.E13 = pyo.Set(initialize=[1, 6, 9, 23], ordered=True)
    model.E12 = pyo.Set(initialize=[2, 5, 14, 19, 20], ordered=True)
    model.E2 = pyo.Set(initialize=[3, 8, 10, 25, 26], ordered=True)
    model.E123 = pyo.Set(
        initialize=[4, 7, 13, 17, 21, 22, 24, 27], ordered=True
    )
    model.E3 = pyo.Set(initialize=[11, 16, 18], ordered=True)
    model.E23 = pyo.Set(initialize=[12], ordered=True)
    model.E1 = pyo.Set(initialize=[15, 20], ordered=True)

    model.cost_team1 = pyo.Param(
        initialize=params["cost_team1"], within=pyo.Reals
    )
    model.cost_team2 = pyo.Param(
        initialize=params["cost_team2"], within=pyo.Reals
    )
    model.cost_team3 = pyo.Param(
        initialize=params["cost_team3"], within=pyo.Reals
    )
    model.rhs_1_3 = pyo.Param(
        initialize=params["rhs_1_3"], within=pyo.Reals
    )
    model.rhs_1_2 = pyo.Param(
        initialize=params["rhs_1_2"], within=pyo.Reals
    )
    model.rhs_2_only = pyo.Param(
        initialize=params["rhs_2_only"], within=pyo.Reals
    )
    model.rhs_1_2_3 = pyo.Param(
        initialize=params["rhs_1_2_3"], within=pyo.Reals
    )
    model.rhs_3_only = pyo.Param(
        initialize=params["rhs_3_only"], within=pyo.Reals
    )
    model.rhs_2_3 = pyo.Param(
        initialize=params["rhs_2_3"], within=pyo.Reals
    )
    model.rhs_1_only = pyo.Param(
        initialize=params["rhs_1_only"], within=pyo.Reals
    )

    model.Selected = pyo.Var(model.Teams, domain=pyo.Binary)

    model.MultiCover_1_3 = pyo.Constraint(
        model.E13,
        rule=lambda mdl, event: (
            mdl.Selected[1] + mdl.Selected[3] >= mdl.rhs_1_3
        ),
    )
    model.MultiCover_1_2 = pyo.Constraint(
        model.E12,
        rule=lambda mdl, event: (
            mdl.Selected[1] + mdl.Selected[2] >= mdl.rhs_1_2
        ),
    )
    model.MultiCover_2_only = pyo.Constraint(
        model.E2,
        rule=lambda mdl, event: mdl.Selected[2] >= mdl.rhs_2_only,
    )
    model.MultiCover_1_2_3 = pyo.Constraint(
        model.E123,
        rule=lambda mdl, event: (
            mdl.Selected[1] + mdl.Selected[2] + mdl.Selected[3]
            >= mdl.rhs_1_2_3
        ),
    )
    model.MultiCover_3_only = pyo.Constraint(
        model.E3,
        rule=lambda mdl, event: mdl.Selected[3] >= mdl.rhs_3_only,
    )
    model.MultiCover_2_3 = pyo.Constraint(
        model.E23,
        rule=lambda mdl, event: (
            mdl.Selected[2] + mdl.Selected[3] >= mdl.rhs_2_3
        ),
    )
    # Event 20 intentionally appears in both applicable constraint families.
    model.MultiCover_1_only = pyo.Constraint(
        model.E1,
        rule=lambda mdl, event: mdl.Selected[1] >= mdl.rhs_1_only,
    )

    model.TotalCost = pyo.Objective(
        expr=(
            model.cost_team1 * model.Selected[1]
            + model.cost_team2 * model.Selected[2]
            + model.cost_team3 * model.Selected[3]
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPsi raises this error when it cannot load a feasible solution.
        # Unexpected runtime errors remain visible to the caller.
        if "a feasible solution was not found" not in str(error).lower():
            raise

    try:
        obj_val = float(pyo.value(model.TotalCost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}