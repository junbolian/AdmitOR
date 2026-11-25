import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    value = params["value"]
    weight = params["weight"]
    capacity = params["capacity"]
    n = params["num_packages"]

    model = pyo.ConcreteModel()

    model.PACKAGES = pyo.Set(initialize=range(n))

    model.select = pyo.Var(model.PACKAGES, within=pyo.Binary)

    model.total_value = pyo.Objective(
        expr=sum(value[i] * model.select[i] for i in model.PACKAGES),
        sense=pyo.maximize,
    )

    model.weight_limit = pyo.Constraint(
        expr=sum(weight[i] * model.select[i] for i in model.PACKAGES) <= capacity
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_value))
    return {"objective": obj_val, "status": "optimal"}