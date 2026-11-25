import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    pattern_yields = params["pattern_yields"]
    demands = params["demands"]
    pattern_upper_bounds = params["pattern_upper_bounds"]

    clients = list(range(4))
    patterns = list(range(10))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=patterns)
    model.C = pyo.Set(initialize=clients)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    model.obj = pyo.Objective(expr=sum(model.x[p] for p in model.P), sense=pyo.minimize)

    model.ub_con = pyo.Constraint(
        model.P,
        rule=lambda m, p: m.x[p] <= pattern_upper_bounds[p]
    )

    model.demand_con = pyo.Constraint(
        model.C,
        rule=lambda m, c: sum(pattern_yields[p][c] * m.x[p] for p in m.P) >= demands[c]
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as e:
        return {"objective": None, "status": str(e)}