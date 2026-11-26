import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    time0_outflow = params["time0_outflow"]
    time1_outflow = params["time1_outflow"]
    npv = params["npv"]
    budget_time0 = params["budget_time0"]
    budget_time1 = params["budget_time1"]

    n = len(time0_outflow)
    investments = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(investments, bounds=(0, 1), initialize=0.0)

    model.time0_con = pyo.Constraint(
        expr=sum(time0_outflow[i] * model.x[i] for i in investments) <= budget_time0
    )
    model.time1_con = pyo.Constraint(
        expr=sum(time1_outflow[i] * model.x[i] for i in investments) <= budget_time1
    )

    model.profit = pyo.Objective(
        expr=sum(npv[i] * model.x[i] for i in investments),
        sense=pyo.maximize,
    )

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.profit))
    except Exception:
        return {"objective": None, "status": "infeasible or failed"}

    return {"objective": obj_val, "status": "optimal"}