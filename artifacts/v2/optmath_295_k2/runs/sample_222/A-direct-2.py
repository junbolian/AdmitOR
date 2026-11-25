import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    value = params["value"]
    weight = params["weight"]
    capacity = params["capacity"]
    num_packages = params["num_packages"]

    packages = list(range(num_packages))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(packages, domain=pyo.Binary)

    def objective_rule(m):
        return sum(value[i] * m.x[i] for i in packages)

    model.total_value = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def weight_rule(m):
        return sum(weight[i] * m.x[i] for i in packages) <= capacity

    model.weight_limit = pyo.Constraint(rule=weight_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_value))
    return {"objective": obj_val, "status": "optimal"}