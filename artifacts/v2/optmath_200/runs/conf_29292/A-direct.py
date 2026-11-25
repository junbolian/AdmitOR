import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    component_cost = params["component_cost"]
    coverage_requirement = params["coverage_requirement"]
    num_components = params["num_components"]
    num_elements = params["num_elements"]

    # Coverage: for each element (1..14), list of component indices (1..15) that can cover it
    covers = {
        1: [1, 6, 8, 13],
        2: [5, 11, 13, 15],
        3: [2, 3, 5, 6, 7, 9],
        4: [2, 3, 7, 8, 11],
        5: [1, 4, 10, 11, 12],
        6: [1, 3, 6, 7, 9, 11, 13],
        7: [2, 4, 13],
        8: [9, 13, 14],
        9: [3, 4, 6, 9, 13],
        10: [3, 7, 12, 13],
        11: [4, 10, 12, 13, 14],
        12: [4, 8, 12],
        13: [1, 2, 5, 15],
        14: [1, 2, 4, 10, 13],
    }

    model = pyo.ConcreteModel()
    model.components = pyo.Set(initialize=list(range(1, num_components + 1)))
    model.elements = pyo.Set(initialize=list(range(1, num_elements + 1)))

    model.x = pyo.Var(model.components, within=pyo.Binary)

    def objective_rule(m):
        return sum(component_cost[i - 1] * m.x[i] for i in m.components)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def coverage_rule(m, e):
        return sum(m.x[c] for c in covers[e]) >= coverage_requirement[e - 1]

    model.coverage = pyo.Constraint(model.elements, rule=coverage_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}