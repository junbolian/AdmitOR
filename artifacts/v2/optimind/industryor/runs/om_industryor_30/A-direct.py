import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    workshops = ["A", "B", "C", "D"]
    components = [1, 2, 3]

    capacity_list = params["capacity"]
    capacity = {w: capacity_list[i] for i, w in enumerate(workshops)}

    rates = {
        "A": params["rate_A"],
        "B": params["rate_B"],
        "C": params["rate_C"],
        "D": params["rate_D"],
    }

    model = pyo.ConcreteModel()

    model.W = pyo.Set(initialize=workshops)
    model.C = pyo.Set(initialize=components)

    model.hours = pyo.Var(model.W, model.C, domain=pyo.NonNegativeReals)

    model.x = pyo.Var(domain=pyo.NonNegativeReals)

    def capacity_rule(m, w):
        return sum(m.hours[w, c] for c in m.C) <= capacity[w]

    model.capacity_con = pyo.Constraint(model.W, rule=capacity_rule)

    def comp_rule(m, c):
        return sum(rates[w][c - 1] * m.hours[w, c] for w in m.W) >= m.x

    model.component_con = pyo.Constraint(model.C, rule=comp_rule)

    model.obj = pyo.Objective(expr=model.x, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}