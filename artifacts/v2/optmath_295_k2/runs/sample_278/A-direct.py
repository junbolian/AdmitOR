import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]

    item_ids = list(range(len(values)))

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=item_ids, ordered=True)
    model.pick = pyo.Var(model.item_set, domain=pyo.Binary)

    model.total_value = pyo.Objective(
        expr=sum(values[i] * model.pick[i] for i in model.item_set),
        sense=pyo.maximize,
    )

    model.weight_capacity = pyo.Constraint(
        expr=sum(weights[i] * model.pick[i] for i in model.item_set) <= capacity
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_value))
    return {"objective": obj_val, "status": "optimal"}