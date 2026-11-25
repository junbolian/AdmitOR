import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    construction_cost = params["construction_cost"]
    demand = params["demand"]
    bonus = params["bonus"]
    R1 = params["R1"]
    R2 = params["R2"]

    dist = [
        [7, 50, 103, 64, 66, 55, 25, 92, 10, 48, 48, 47, 78, 36],
        [43, 18, 70, 18, 57, 43, 27, 96, 48, 39, 28, 72, 81, 60],
        [68, 62, 69, 96, 27, 37, 63, 20, 62, 40, 51, 32, 7, 37],
        [18, 38, 84, 63, 43, 33, 19, 70, 14, 27, 31, 30, 55, 17],
        [107, 64, 20, 74, 64, 65, 89, 92, 108, 70, 66, 107, 84, 100],
        [66, 61, 70, 95, 27, 37, 62, 22, 61, 39, 51, 30, 9, 35],
        [58, 20, 39, 49, 25, 17, 41, 65, 58, 21, 17, 60, 51, 52],
        [94, 80, 67, 114, 42, 56, 87, 9, 89, 61, 71, 58, 20, 63],
        [6, 49, 102, 62, 66, 54, 24, 93, 11, 47, 47, 48, 79, 37],
        [48, 27, 52, 61, 13, 3, 35, 51, 46, 8, 17, 41, 36, 33],
        [53, 67, 93, 98, 47, 48, 56, 46, 45, 47, 57, 8, 37, 21],
        [83, 78, 78, 112, 41, 53, 79, 9, 77, 57, 68, 43, 15, 51],
        [54, 10, 48, 34, 39, 27, 35, 80, 56, 27, 17, 67, 65, 57],
        [72, 31, 50, 28, 59, 50, 54, 99, 76, 50, 40, 91, 86, 80],
        [43, 10, 63, 25, 48, 34, 25, 88, 47, 31, 20, 67, 73, 55],
        [30, 16, 72, 34, 47, 33, 12, 85, 34, 27, 19, 57, 69, 44],
        [55, 12, 48, 32, 42, 30, 37, 82, 58, 30, 20, 70, 68, 60],
        [100, 57, 15, 70, 57, 58, 82, 86, 101, 63, 59, 100, 78, 93],
        [28, 17, 69, 44, 38, 24, 11, 74, 29, 17, 14, 46, 59, 34],
        [75, 74, 81, 108, 40, 50, 72, 18, 68, 52, 63, 33, 17, 42],
    ]

    nodes = list(range(20))
    sites = list(range(14))

    def within_r1(i, j):
        return dist[i][j] <= R1

    def within_r2(i, j):
        return dist[i][j] <= R2

    model = pyo.ConcreteModel()

    model.x = pyo.Var(sites, domain=pyo.Binary)
    model.z = pyo.Var(nodes, domain=pyo.Binary)

    # SLA: each node covered within R1
    def cover_rule(model, i):
        return sum(model.x[j] for j in sites if within_r1(i, j)) >= 1

    model.cover_con = pyo.Constraint(nodes, rule=cover_rule)

    # z_i <= sum of x_j within R2 -> bonus only earned if ultra-fast access
    def bonus_rule(model, i):
        return model.z[i] <= sum(model.x[j] for j in sites if within_r2(i, j))

    model.bonus_con = pyo.Constraint(nodes, rule=bonus_rule)

    def net_cost_rule(model):
        return sum(construction_cost[j] * model.x[j] for j in sites) - sum(
            bonus[i] * model.z[i] for i in nodes
        )

    model.net_cost = pyo.Objective(rule=net_cost_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.net_cost))
    return {"objective": obj_val, "status": "optimal"}