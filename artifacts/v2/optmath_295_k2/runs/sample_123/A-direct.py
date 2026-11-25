import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    population = params["population"]
    tower_cost = params["tower_cost"]
    budget = params["budget"]

    regions = list(range(10))
    towers = list(range(7))

    region_towers = {
        0: [0, 3, 5, 6],
        1: [2, 3, 4, 6],
        2: [0, 1, 4, 5, 6],
        3: [0, 3, 4],
        4: [0, 3, 4],
        5: [1, 2, 3],
        6: [1, 2, 3, 4],
        7: [1, 2, 3, 4, 5, 6],
        8: [0, 1, 2, 4, 5],
        9: [1, 4, 6],
    }

    model = pyo.ConcreteModel()

    model.TOWERS = pyo.Set(initialize=towers)
    model.REGIONS = pyo.Set(initialize=regions)

    model.build_tower = pyo.Var(model.TOWERS, domain=pyo.Binary)
    model.cover_region = pyo.Var(model.REGIONS, domain=pyo.Binary)

    def budget_rule(m):
        return sum(tower_cost[t] * m.build_tower[t] for t in m.TOWERS) <= budget
    model.budget_con = pyo.Constraint(rule=budget_rule)

    def cover_rule(m, r):
        return m.cover_region[r] <= sum(m.build_tower[t] for t in region_towers[r])
    model.cover_con = pyo.Constraint(model.REGIONS, rule=cover_rule)

    def obj_rule(m):
        return sum(population[r] * m.cover_region[r] for r in m.REGIONS)
    model.total_population = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_population))
    return {"objective": obj_val, "status": "optimal"}