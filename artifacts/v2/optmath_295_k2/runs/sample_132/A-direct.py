import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost_team1 = params["cost_team1"]
    cost_team2 = params["cost_team2"]
    cost_team3 = params["cost_team3"]

    coef_sel1_sel3 = params["coef_sel1_sel3"]
    rhs_sel1_sel3 = params["rhs_sel1_sel3"]
    coef_sel1_sel2 = params["coef_sel1_sel2"]
    rhs_sel1_sel2 = params["rhs_sel1_sel2"]
    coef_sel2_single = params["coef_sel2_single"]
    rhs_sel2_single = params["rhs_sel2_single"]
    coef_all_three = params["coef_all_three"]
    rhs_all_three = params["rhs_all_three"]
    coef_sel3_single = params["coef_sel3_single"]
    rhs_sel3_single = params["rhs_sel3_single"]
    coef_sel2_sel3 = params["coef_sel2_sel3"]
    rhs_sel2_sel3 = params["rhs_sel2_sel3"]
    coef_sel1_single = params["coef_sel1_single"]
    rhs_sel1_single = params["rhs_sel1_single"]

    model = pyo.ConcreteModel()

    model.TEAMS = pyo.Set(initialize=[1, 2, 3])

    model.Selected = pyo.Var(model.TEAMS, domain=pyo.Binary)

    def cost_rule(m):
        return (cost_team1 * m.Selected[1]
                + cost_team2 * m.Selected[2]
                + cost_team3 * m.Selected[3])

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    e_sel1_sel3 = list(range(4))
    e_sel1_sel2 = list(range(5))
    e_sel2_single = list(range(5))
    e_all_three = list(range(8))
    e_sel3_single = list(range(3))
    e_sel2_sel3 = list(range(1))
    e_sel1_single = list(range(2))

    model.C_SEL1_SEL3 = pyo.Constraint(
        e_sel1_sel3,
        rule=lambda m, e: coef_sel1_sel3 * (m.Selected[1] + m.Selected[3]) >= rhs_sel1_sel3,
    )
    model.C_SEL1_SEL2 = pyo.Constraint(
        e_sel1_sel2,
        rule=lambda m, e: coef_sel1_sel2 * (m.Selected[1] + m.Selected[2]) >= rhs_sel1_sel2,
    )
    model.C_SEL2_SINGLE = pyo.Constraint(
        e_sel2_single,
        rule=lambda m, e: coef_sel2_single * m.Selected[2] >= rhs_sel2_single,
    )
    model.C_ALL_THREE = pyo.Constraint(
        e_all_three,
        rule=lambda m, e: coef_all_three * (m.Selected[1] + m.Selected[2] + m.Selected[3]) >= rhs_all_three,
    )
    model.C_SEL3_SINGLE = pyo.Constraint(
        e_sel3_single,
        rule=lambda m, e: coef_sel3_single * m.Selected[3] >= rhs_sel3_single,
    )
    model.C_SEL2_SEL3 = pyo.Constraint(
        e_sel2_sel3,
        rule=lambda m, e: coef_sel2_sel3 * (m.Selected[2] + m.Selected[3]) >= rhs_sel2_sel3,
    )
    model.C_SEL1_SINGLE = pyo.Constraint(
        e_sel1_single,
        rule=lambda m, e: coef_sel1_single * m.Selected[1] >= rhs_sel1_single,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}