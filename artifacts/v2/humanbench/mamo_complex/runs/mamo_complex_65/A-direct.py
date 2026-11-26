import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    time0_outflow = params["time0_outflow"]
    time1_outflow = params["time1_outflow"]
    npv = params["npv"]
    budget_time0 = params["budget_time0"]
    budget_time1 = params["budget_time1"]

    investments = list(range(len(npv)))

    model = pyo.ConcreteModel()

    model.invest = pyo.Var(investments, bounds=(0, 1))

    model.time0_constraint = pyo.Constraint(
        expr=sum(time0_outflow[i] * model.invest[i] for i in investments)
        <= budget_time0
    )
    model.time1_constraint = pyo.Constraint(
        expr=sum(time1_outflow[i] * model.invest[i] for i in investments)
        <= budget_time1
    )

    model.obj = pyo.Objective(
        expr=sum(npv[i] * model.invest[i] for i in investments),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}