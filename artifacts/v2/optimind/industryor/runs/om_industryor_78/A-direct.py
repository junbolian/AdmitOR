import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    wage_skilled = params["wage_skilled"]
    wage_laborer = params["wage_laborer"]
    eff_sk = params["effective_hours_skilled"]
    eff_lb = params["effective_hours_laborer"]
    d1 = params["demand_task1"]
    d2 = params["demand_task2"]
    d3 = params["demand_task3"]
    max_sk = params["max_skilled"]
    max_lb = params["max_laborers"]

    model = pyo.ConcreteModel()

    # Total workers hired
    model.S = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, max_sk))
    model.L = pyo.Var(domain=pyo.NonNegativeReals, bounds=(0, max_lb))

    # Activity levels for each task completion mode
    # Task 1: x1a = skilled alone; x1b = 1 skilled + 2 laborers
    # Task 2: x2a = skilled alone; x2b = laborer alone
    # Task 3: x3a = 5 laborers; x3b = 1 skilled + 3 laborers
    model.x1a = pyo.Var(domain=pyo.NonNegativeReals)
    model.x1b = pyo.Var(domain=pyo.NonNegativeReals)
    model.x2a = pyo.Var(domain=pyo.NonNegativeReals)
    model.x2b = pyo.Var(domain=pyo.NonNegativeReals)
    model.x3a = pyo.Var(domain=pyo.NonNegativeReals)
    model.x3b = pyo.Var(domain=pyo.NonNegativeReals)

    # Effective hours delivered by a skilled worker / laborer on each mode:
    # A skilled worker contributes eff_sk effective hours; a laborer eff_lb.
    # Task 1 requirements (effective hours):
    model.c1a = pyo.Constraint(expr=eff_sk * model.x1a + eff_sk * model.x1b >= d1)
    model.c1b = pyo.Constraint(expr=2 * eff_lb * model.x1b <= 2 * eff_sk * model.x1b)  # structural, always true; skip

    # Instead model per-group effective hours directly.
    # Rewrite: each "x1a" unit = 1 skilled (eff_sk hours). Each "x1b" unit = 1 skilled + 2 laborers.
    # Effective hours from one x1b unit = eff_sk + 2*eff_lb.
    # We need demand in effective hours, so group contributes its full effective hours.
    # Remove the redundant constraint above by not creating it.

    del model.c1a
    del model.c1b

    # Task 1 demand (effective hours)
    model.task1 = pyo.Constraint(
        expr=eff_sk * model.x1a + (eff_sk + 2 * eff_lb) * model.x1b >= d1
    )
    # Task 2 demand
    model.task2 = pyo.Constraint(
        expr=eff_sk * model.x2a + eff_lb * model.x2b >= d2
    )
    # Task 3 demand
    model.task3 = pyo.Constraint(
        expr=5 * eff_lb * model.x3a + (eff_sk + 3 * eff_lb) * model.x3b >= d3
    )

    # Skilled worker balance: total skilled used <= hired
    model.skilled_bal = pyo.Constraint(
        expr=model.x1a + model.x1b + model.x2a + model.x3b <= model.S
    )
    # Laborer balance: total laborers used <= hired
    model.laborer_bal = pyo.Constraint(
        expr=2 * model.x1b + model.x2b + 5 * model.x3a + 3 * model.x3b <= model.L
    )

    model.obj = pyo.Objective(
        expr=wage_skilled * model.S + wage_laborer * model.L,
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}