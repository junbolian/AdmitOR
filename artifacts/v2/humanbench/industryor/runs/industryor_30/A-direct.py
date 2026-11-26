import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    acts = ["A", "B", "C", "D", "E", "F", "G"]
    dur = {
        "A": params["duration_A"],
        "B": params["duration_B"],
        "C": params["duration_C"],
        "D": params["duration_D"],
        "E": params["duration_E"],
        "F": params["duration_F"],
        "G": params["duration_G"],
    }
    # precedence: predecessor -> successors
    preds = {
        "A": [],
        "B": ["F"],
        "C": ["D", "F"],
        "D": ["A"],
        "E": [],
        "F": ["E", "G"],
        "G": ["A"],
    }

    model = pyo.ConcreteModel()

    model.ACTS = pyo.Set(initialize=acts)
    model.S = pyo.Var(model.ACTS, domain=pyo.NonNegativeReals)
    model.T = pyo.Var(domain=pyo.NonNegativeReals)

    def end_expr(j):
        return model.S[j] + dur[j]

    # precedence constraints
    def prec_rule(model, i, j):
        return model.S[i] + dur[i] <= model.S[j]

    model.prec = pyo.Constraint(
        [(i, j) for j in acts for i in preds[j]], rule=prec_rule
    )

    # makespan
    model.mk = pyo.ConstraintList()
    for j in acts:
        model.mk.add(end_expr(j) <= model.T)

    # machinery active from start of A to end of B
    model.mach = pyo.Constraint(expr=model.T >= model.S["B"] + dur["B"] - model.S["A"])

    # objective: work cost on makespan + machinery cost over span
    machinery_span = (model.S["B"] + dur["B"]) - model.S["A"]
    model.obj = pyo.Objective(
        expr=params["daily_work_cost"] * model.T + params["daily_machinery_cost"] * machinery_span,
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}