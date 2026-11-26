import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    a_j = list(params["a_j"])
    k = params["k"]
    n = len(a_j)

    model = pyo.ConcreteModel()
    model.YEARS = pyo.RangeSet(1, n)

    # x[j]: jets allocated to combat in year j
    # t[j]: jets allocated to training in year j
    model.x = pyo.Var(model.YEARS, within=pyo.NonNegativeReals)
    model.t = pyo.Var(model.YEARS, within=pyo.NonNegativeReals)

    # Production allocation constraint each year
    def alloc_rule(m, j):
        return m.x[j] + m.t[j] <= a_j[j - 1]
    model.alloc = pyo.Constraint(model.YEARS, rule=alloc_rule)

    # Pilot training capacity: k pilots per training jet per year.
    # Combat jets require pilots; cumulative pilots trained by year j must
    # support cumulative combat jets deployed up to year j.
    def pilot_rule(m, j):
        return sum(m.x[i] for i in model.YEARS if i <= j) <= sum(
            k * m.t[i] for i in model.YEARS if i <= j
        )
    model.pilot = pyo.Constraint(model.YEARS, rule=pilot_rule)

    # Objective: maximize cumulative combat contribution
    def obj_rule(m):
        return sum(m.x[j] for j in model.YEARS)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}