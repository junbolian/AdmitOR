import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_team1 = params["cost_team1"]
    cost_team2 = params["cost_team2"]
    cost_team3 = params["cost_team3"]

    rhs_1_3 = params["rhs_1_3"]
    rhs_1_2 = params["rhs_1_2"]
    rhs_2_only = params["rhs_2_only"]
    rhs_1_2_3 = params["rhs_1_2_3"]
    rhs_3_only = params["rhs_3_only"]
    rhs_2_3 = params["rhs_2_3"]
    rhs_1_only = params["rhs_1_only"]

    model = pyo.ConcreteModel()

    model.TEAMS = pyo.Set(initialize=[1, 2, 3])
    model.Selected = pyo.Var(model.TEAMS, within=pyo.Binary)

    # Objective
    cost_map = {1: cost_team1, 2: cost_team2, 3: cost_team3}
    model.total_cost = pyo.Objective(
        expr=sum(cost_map[t] * model.Selected[t] for t in model.TEAMS),
        sense=pyo.minimize,
    )

    # Constraints
    model.c_1_3 = pyo.ConstraintList()
    for _ in range(4):
        model.c_1_3.add(model.Selected[1] + model.Selected[3] >= rhs_1_3)

    model.c_1_2 = pyo.ConstraintList()
    for _ in range(5):
        model.c_1_2.add(model.Selected[1] + model.Selected[2] >= rhs_1_2)

    model.c_2_only = pyo.ConstraintList()
    for _ in range(5):
        model.c_2_only.add(model.Selected[2] >= rhs_2_only)

    model.c_1_2_3 = pyo.ConstraintList()
    for _ in range(8):
        model.c_1_2_3.add(
            model.Selected[1] + model.Selected[2] + model.Selected[3] >= rhs_1_2_3
        )

    model.c_3_only = pyo.ConstraintList()
    for _ in range(3):
        model.c_3_only.add(model.Selected[3] >= rhs_3_only)

    model.c_2_3 = pyo.ConstraintList()
    for _ in range(1):
        model.c_2_3.add(model.Selected[2] + model.Selected[3] >= rhs_2_3)

    model.c_1_only = pyo.ConstraintList()
    for _ in range(2):
        model.c_1_only.add(model.Selected[1] >= rhs_1_only)

    # Solve
    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}