import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    populations = params["populations"]
    tower_costs = params["tower_costs"]
    budget = params["budget"]
    coverage_links = params["coverage_links"]
    num_areas = params["num_areas"]
    num_towers = params["num_towers"]

    areas = list(range(num_areas))
    towers = list(range(num_towers))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(towers, domain=pyo.Binary)
    model.y = pyo.Var(areas, domain=pyo.Binary)

    def obj_rule(m):
        return sum(populations[i] * m.y[i] for i in areas)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def budget_rule(m):
        return sum(tower_costs[j] * m.x[j] for j in towers) <= budget

    model.budget_con = pyo.Constraint(rule=budget_rule)

    def coverage_rule(m, i):
        return m.y[i] <= sum(coverage_links[i][j] * m.x[j] for j in towers)

    model.coverage_con = pyo.Constraint(areas, rule=coverage_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}