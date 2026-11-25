import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    min_contributors = params["min_contributors"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    num_prod = len(capacity)
    num_contracts = len(demand)

    producers = list(range(num_prod))
    contracts = list(range(num_contracts))

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=producers)
    model.C = pyo.Set(initialize=contracts)
    model.PC = pyo.Set(initialize=[(i, j) for i in producers for j in contracts], dimen=2)

    model.x = pyo.Var(model.PC, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.PC, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i, j in m.PC)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.P) >= demand[j]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.C) <= capacity[i]

    model.capacity_con = pyo.Constraint(model.P, rule=capacity_rule)

    def link_lower_rule(m, i, j):
        return m.x[i, j] >= min_delivery[i] * m.y[i, j]

    model.link_lower = pyo.Constraint(model.PC, rule=link_lower_rule)

    def link_upper_rule(m, i, j):
        big_m = min(capacity[i], demand[j])
        return m.x[i, j] <= big_m * m.y[i, j]

    model.link_upper = pyo.Constraint(model.PC, rule=link_upper_rule)

    def min_contr_val(j):
        return min_contributors if isinstance(min_contributors, (int, float)) else min_contributors[j]

    def contrib_rule(m, j):
        return sum(m.y[i, j] for i in m.P) >= min_contr_val(j)

    model.contrib_con = pyo.Constraint(model.C, rule=contrib_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}