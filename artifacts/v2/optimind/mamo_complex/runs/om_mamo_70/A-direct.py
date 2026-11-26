import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost_matrix = params["cost_matrix"]

    n = len(supply)
    clinics = list(range(n))

    model = pyo.ConcreteModel()

    model.clinics = pyo.Set(initialize=clinics)

    model.x = pyo.Var(
        model.clinics, model.clinics, domain=pyo.NonNegativeReals
    )

    model.obj = pyo.Objective(
        expr=sum(
            cost_matrix[i][j] * model.x[i, j]
            for i in clinics
            for j in clinics
            if i != j
        ),
        sense=pyo.minimize,
    )

    def balance_rule(mdl, i):
        outflow = sum(mdl.x[i, j] for j in clinics if j != i)
        inflow = sum(mdl.x[j, i] for j in clinics if j != i)
        return supply[i] - outflow + inflow >= demand[i]

    model.balance = pyo.Constraint(model.clinics, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}