import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    workshops = ["A", "B", "C", "D"]
    components = [1, 2, 3]
    comp_index = {1: 0, 2: 1, 3: 2}

    capacity = {
        "A": params["capacity_A"],
        "B": params["capacity_B"],
        "C": params["capacity_C"],
        "D": params["capacity_D"],
    }
    productivity = {
        "A": params["productivity_A"],
        "B": params["productivity_B"],
        "C": params["productivity_C"],
        "D": params["productivity_D"],
    }

    model = pyo.ConcreteModel()

    model.W = pyo.Set(initialize=workshops)
    model.COMP = pyo.Set(initialize=components)

    model.hours = pyo.Var(model.W, model.COMP, domain=pyo.NonNegativeReals)
    model.products = pyo.Var(domain=pyo.NonNegativeReals)

    def cap_rule(mdl, w):
        return sum(mdl.hours[w, c] for c in components) <= capacity[w]
    model.cap_con = pyo.Constraint(model.W, rule=cap_rule)

    def comp_rule(mdl, c):
        return sum(
            productivity[w][comp_index[c]] * mdl.hours[w, c] for w in workshops
        ) >= mdl.products
    model.comp_con = pyo.Constraint(model.COMP, rule=comp_rule)

    model.obj = pyo.Objective(expr=model.products, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}