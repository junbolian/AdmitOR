import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = {
        1: params["cost_v1"],
        2: params["cost_v2"],
        3: params["cost_v3"],
        4: params["cost_v4"],
        5: params["cost_v5"],
    }

    vehicles = [1, 2, 3, 4, 5]

    coverage = {
        "e1": [4, 5],
        "e2": [4, 5],
        "e3": [3],
        "e4": [1, 2],
        "e5": [1, 2, 4],
        "e6": [1, 3, 4],
        "e7": [3, 4, 5],
        "e8": [3, 4],
        "e9": [1, 2, 3],
        "e10": [3, 4, 5],
        "e11": [3, 5],
        "e12": [1],
        "e13": [1, 4, 5],
        "e14": [3, 4],
        "e15": [1, 2, 5],
        "e16": [1, 2],
        "e17": [2],
        "e18": [5],
        "e19": [1, 4],
        "e20": [2],
        "e21": [3, 4, 5],
        "e22": [5],
        "e23": [1, 4],
        "e24": [2, 5],
        "e25": [1, 3, 5],
        "e26": [1, 2, 3],
        "e27": [5],
        "e28": [2, 4],
        "e29": [1, 3],
        "e30": [5],
        "e31": [1, 3],
    }

    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=vehicles)
    model.R = pyo.Set(initialize=list(coverage.keys()))

    model.x = pyo.Var(model.V, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[v] * m.x[v] for v in m.V)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def coverage_rule(m, r):
        return sum(m.x[v] for v in coverage[r]) >= 1

    model.cover = pyo.Constraint(model.R, rule=coverage_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}