import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_weights = params["supply_weights"]
    capacity = params["hospital_capacity"]

    n_supplies = len(supply_weights)
    n_hospitals = n_supplies  # one hospital per supply is a safe upper bound

    model = pyo.ConcreteModel()

    model.SUP = pyo.RangeSet(0, n_supplies - 1)
    model.HOSP = pyo.RangeSet(0, n_hospitals - 1)

    model.x = pyo.Var(model.SUP, model.HOSP, domain=pyo.Binary)
    model.y = pyo.Var(model.HOSP, domain=pyo.Binary)

    # Objective: minimize number of hospitals used
    model.obj = pyo.Objective(
        expr=sum(model.y[j] for j in model.HOSP),
        sense=pyo.minimize,
    )

    # Each supply assigned to exactly one hospital
    model.assign = pyo.Constraint(
        model.SUP,
        rule=lambda m, i: sum(m.x[i, j] for j in m.HOSP) == 1,
    )

    # Capacity constraints
    model.cap = pyo.Constraint(
        model.HOSP,
        rule=lambda m, j: sum(supply_weights[i] * m.x[i, j] for i in m.SUP)
        <= capacity * m.y[j],
    )

    # Symmetry-breaking: hospital j can only be used if hospital j-1 is used
    model.sym = pyo.Constraint(
        model.HOSP,
        rule=lambda m, j: m.y[j] <= m.y[j - 1] if j >= 1 else pyo.Constraint.Skip,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}