import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_contributors = params["min_contributors"]
    min_delivery = params["min_delivery"]
    n_producers = int(params["n_producers"])
    n_contracts = int(params["n_contracts"])

    producers = list(range(n_producers))
    contracts = list(range(n_contracts))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=producers, ordered=True)
    model.C = pyo.Set(initialize=contracts, ordered=True)
    model.PC = pyo.Set(initialize=[(i, j) for i in producers for j in contracts], dimen=2)

    model.x = pyo.Var(model.PC, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.PC, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in producers for j in contracts)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cap_rule(m, i):
        return sum(m.x[i, j] for j in contracts) <= capacity[i]

    model.cap_con = pyo.Constraint(model.P, rule=cap_rule)

    def dem_rule(m, j):
        return sum(m.x[i, j] for i in producers) >= demand[j]

    model.dem_con = pyo.Constraint(model.C, rule=dem_rule)

    def contrib_rule(m, j):
        return sum(m.y[i, j] for i in producers) >= min_contributors[j]

    model.contrib_con = pyo.Constraint(model.C, rule=contrib_rule)

    def min_del_rule(m, i, j):
        return m.x[i, j] >= min_delivery[i] * m.y[i, j]

    model.min_del_con = pyo.Constraint(model.PC, rule=min_del_rule)

    def upper_rule(m, i, j):
        return m.x[i, j] <= capacity[i] * m.y[i, j]

    model.upper_con = pyo.Constraint(model.PC, rule=upper_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}