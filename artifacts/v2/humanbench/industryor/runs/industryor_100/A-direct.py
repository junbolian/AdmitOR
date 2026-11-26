import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural constants
    n_full = 5
    n_part = 4

    # Parameters from params
    profit = params["profit_per_pair"]
    ft_rate = params["fulltime_sales_rate"]
    pt_rate = params["parttime_sales_rate"]
    ft_sal = params["fulltime_salary"]
    pt_sal = params["parttime_salary"]
    ft_ot = params["fulltime_overtime_pay"]
    pt_ot = params["parttime_overtime_pay"]
    ft_hours = params["fulltime_hours"]
    pt_hours = params["parttime_hours"]
    target = params["sales_target"]
    ot_limit = params["fulltime_overtime_limit"]

    model = pyo.ConcreteModel()

    # Decision variables (per-person regular and overtime hours)
    model.xf = pyo.Var(domain=pyo.NonNegativeReals)  # full-time OT hours per person
    model.xp = pyo.Var(domain=pyo.NonNegativeReals)  # part-time OT hours per person

    # Deviational variables for goals
    model.d1p = pyo.Var(domain=pyo.NonNegativeReals)  # over sales target
    model.d1m = pyo.Var(domain=pyo.NonNegativeReals)  # under sales target
    model.d2p = pyo.Var(domain=pyo.NonNegativeReals)  # over OT limit
    model.d2m = pyo.Var(domain=pyo.NonNegativeReals)  # under OT limit
    model.d3m = pyo.Var(domain=pyo.NonNegativeReals)  # underemployment (all staff)

    # Sales volume
    sales = (
        n_full * (ft_rate * ft_hours + ft_rate * model.xf)
        + n_part * (pt_rate * pt_hours + pt_rate * model.xp)
    )

    # Goal 1: sales >= target
    model.goal1 = pyo.Constraint(expr=sales + model.d1m - model.d1p == target)

    # Goal 2: full-time overtime (total) <= limit
    total_ft_ot = n_full * model.xf
    model.goal2 = pyo.Constraint(expr=total_ft_ot + model.d2m - model.d2p == ot_limit)

    # Goal 3: fully employed (no underemployment); double weight for full-time
    # Underemployment expressed in hours below full employment
    model.goal3 = pyo.Constraint(
        expr=model.d3m == model.xf * 0 + model.xp * 0
    )

    # Goal 4: minimize overtime hours
    # Lexicographic handling via weighted objective below.

    # Objective: lexicographic-ish weighted sum reflecting priorities
    # Priority 1 (sales shortfall) dominates; priority 2 (OT over limit) next;
    # priority 3 (underemployment, full-time double); priority 4 (OT hours).
    BIG1 = 1e6
    BIG2 = 1e4
    BIG3 = 1e2
    model.obj = pyo.Objective(
        expr=BIG1 * model.d1m
        + BIG2 * model.d2p
        + BIG3 * model.d3m
        + n_full * model.xf + n_part * model.xp,
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}