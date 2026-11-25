import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _coef(value, pos):
    # value may be a scalar or a sequence of per-constraint coefficients
    if isinstance(value, (list, tuple)):
        return value[pos]
    return value


def solve(params):
    model = pyo.ConcreteModel()

    model.Selected = pyo.Var([1, 2, 3], domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=params["cost_team1"] * model.Selected[1]
        + params["cost_team2"] * model.Selected[2]
        + params["cost_team3"] * model.Selected[3],
        sense=pyo.minimize,
    )

    ids_sel1_sel3 = [1, 6, 9, 23]
    ids_sel1_sel2 = [2, 5, 14, 19, 20]
    ids_sel2_single = [3, 8, 10, 25, 26]
    ids_all_three = [4, 7, 13, 17, 21, 22, 24, 27]
    ids_sel3_single = [11, 16, 18]
    ids_sel2_sel3 = [12]
    ids_sel1_single = [15, 20]

    def rule_sel1_sel3(m, i):
        pos = ids_sel1_sel3.index(i)
        c = _coef(params["coef_sel1_sel3"], pos)
        return c * m.Selected[1] + c * m.Selected[3] >= params["rhs_sel1_sel3"]

    def rule_sel1_sel2(m, i):
        pos = ids_sel1_sel2.index(i)
        c = _coef(params["coef_sel1_sel2"], pos)
        return c * m.Selected[1] + c * m.Selected[2] >= params["rhs_sel1_sel2"]

    def rule_sel2_single(m, i):
        pos = ids_sel2_single.index(i)
        c = _coef(params["coef_sel2_single"], pos)
        return c * m.Selected[2] >= params["rhs_sel2_single"]

    def rule_all_three(m, i):
        pos = ids_all_three.index(i)
        c = _coef(params["coef_all_three"], pos)
        return (c * m.Selected[1] + c * m.Selected[2] + c * m.Selected[3]
                >= params["rhs_all_three"])

    def rule_sel3_single(m, i):
        pos = ids_sel3_single.index(i)
        c = _coef(params["coef_sel3_single"], pos)
        return c * m.Selected[3] >= params["rhs_sel3_single"]

    def rule_sel2_sel3(m, i):
        pos = ids_sel2_sel3.index(i)
        c = _coef(params["coef_sel2_sel3"], pos)
        return c * m.Selected[2] + c * m.Selected[3] >= params["rhs_sel2_sel3"]

    def rule_sel1_single(m, i):
        pos = ids_sel1_single.index(i)
        c = _coef(params["coef_sel1_single"], pos)
        return c * m.Selected[1] >= params["rhs_sel1_single"]

    model.c_sel1_sel3 = pyo.Constraint(ids_sel1_sel3, rule=rule_sel1_sel3)
    model.c_sel1_sel2 = pyo.Constraint(ids_sel1_sel2, rule=rule_sel1_sel2)
    model.c_sel2_single = pyo.Constraint(ids_sel2_single, rule=rule_sel2_single)
    model.c_all_three = pyo.Constraint(ids_all_three, rule=rule_all_three)
    model.c_sel3_single = pyo.Constraint(ids_sel3_single, rule=rule_sel3_single)
    model.c_sel2_sel3 = pyo.Constraint(ids_sel2_sel3, rule=rule_sel2_sel3)
    model.c_sel1_single = pyo.Constraint(ids_sel1_single, rule=rule_sel1_single)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}