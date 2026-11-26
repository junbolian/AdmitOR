import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    requirements = params["requirements"]
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    model = pyo.ConcreteModel()

    # x[j] = number of employees whose two-day-off pair starts such that they
    # work 5 consecutive days beginning on day j (i.e., off days are j+5, j+6)
    model.x = pyo.Var(range(7), domain=pyo.NonNegativeReals)

    # Each shift pattern indexed by start day j covers days j, j+1, ..., j+4 (mod 7)
    def coverage_rule(model, d):
        # sum over shifts that work on day d
        return sum(model.x[j] for j in range(7) if (d - j) % 7 < 5) >= requirements[d]

    model.coverage = pyo.Constraint(range(7), rule=coverage_rule)

    model.obj = pyo.Objective(expr=sum(model.x[j] for j in range(7)), sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}