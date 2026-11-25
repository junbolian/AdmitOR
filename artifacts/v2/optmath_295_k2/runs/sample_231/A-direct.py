import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = [
        params["cost_v1"],
        params["cost_v2"],
        params["cost_v3"],
        params["cost_v4"],
        params["cost_v5"],
    ]
    vehicles = list(range(5))

    coverage = {
        "e1": [3, 4],
        "e2": [3, 4],
        "e3": [2],
        "e4": [0, 1],
        "e5": [0, 1, 3],
        "e6": [0, 2, 3],
        "e7": [2, 3, 4],
        "e8": [2, 3],
        "e9": [0, 1, 2],
        "e10": [2, 3, 4],
        "e11": [2, 4],
        "e12": [0],
        "e13": [0, 3, 4],
        "e14": [2, 3],
        "e15": [0, 1, 4],
        "e16": [0, 1],
        "e17": [1],
        "e18": [4],
        "e19": [0, 3],
        "e20": [1],
        "e21": [2, 3, 4],
        "e22": [4],
        "e23": [0, 3],
        "e24": [1, 4],
        "e25": [0, 2, 4],
        "e26": [0, 1, 2],
        "e27": [4],
        "e28": [1, 3],
        "e29": [0, 2],
        "e30": [4],
        "e31": [0, 2],
    }

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=vehicles)
    model.E = pyo.Set(initialize=list(coverage.keys()))

    model.x = pyo.Var(model.V, domain=pyo.Binary)

    def cost_rule(mdl):
        return sum(costs[i] * mdl.x[i] for i in mdl.V)

    model.cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def cover_rule(mdl, e):
        return sum(mdl.x[i] for i in coverage[e]) >= 1

    model.cover = pyo.Constraint(model.E, rule=cover_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.cost))
    return {"objective": obj_val, "status": "optimal"}