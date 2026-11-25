import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    peaks = list(range(4))
    aminos = list(range(5))

    cost = {}
    for i in peaks:
        for a in aminos:
            cost[i, a] = params[f"cost_peak{i}_aa{a}"]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(peaks, aminos, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[i, a] * model.x[i, a] for i in peaks for a in aminos),
        sense=pyo.minimize,
    )

    model.peak_cap = pyo.ConstraintList()
    for i in peaks:
        model.peak_cap.add(sum(model.x[i, a] for a in aminos) <= 1)

    model.amino_cap = pyo.ConstraintList()
    for a in aminos:
        model.amino_cap.add(sum(model.x[i, a] for i in peaks) <= 1)

    model.num_assign = pyo.Constraint(
        expr=sum(model.x[i, a] for i in peaks for a in aminos) == params["num_assignments"]
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}