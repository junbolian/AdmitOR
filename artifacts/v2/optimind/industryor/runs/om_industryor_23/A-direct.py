import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    C = params["total_capital"]
    r1 = params["return_rate_option1"]
    r2 = params["return_rate_option2"]

    model = pyo.ConcreteModel()

    # Periods (years) 0..3
    model.T = pyo.Set(initialize=[0, 1, 2, 3])

    # x[t]: amount invested at start of year t (t in 0,1,2) in 1-year option
    model.x = pyo.Var(range(3), domain=pyo.NonNegativeReals)
    # y[t]: amount invested at start of year t (t in 0,1) in 2-year option
    model.y = pyo.Var(range(2), domain=pyo.NonNegativeReals)

    # Returns from prior investments available at start of each year
    # At t=0: capital C available
    # At t=1: capital not invested at t0 + r1 * x0
    # At t=2: leftover + r1*x1 + r2*y0
    # At t=3: leftover + r1*x2 + r2*y1

    # Cash-balance constraints
    def cash_balance_rule(m, t):
        if t == 0:
            return m.x[0] + m.y[0] == C
        elif t == 1:
            return m.x[1] + m.y[1] == r1 * m.x[0]
        elif t == 2:
            return m.x[2] == r1 * m.x[1] + r2 * m.y[0]
        else:
            return pyo.Constraint.Skip

    model.cash_balance = pyo.Constraint([0, 1, 2], rule=cash_balance_rule)

    # Final wealth at end of year 3
    def objective_rule(m):
        return r1 * m.x[2] + r2 * m.y[1]

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}