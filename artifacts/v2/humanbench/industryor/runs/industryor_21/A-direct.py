import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    variable_cost = params["variable_cost"]
    fixed_cost = params["fixed_cost"]

    types = list(range(1, 7))

    model = pyo.ConcreteModel()

    model.T = pyo.Set(initialize=types)

    # x[i, j]: amount of type i produced to satisfy demand of container j
    # Allowed only if i has capacity >= capacity of j (i can substitute for j)
    valid_pairs = [(i, j) for i in types for j in types
                   if capacity[i - 1] >= capacity[j - 1]]
    model.PAIRS = pyo.Set(initialize=valid_pairs, dimen=2)

    model.x = pyo.Var(model.PAIRS, domain=pyo.NonNegativeReals)
    # y[i]: 1 if type i is produced (fixed cost incurred)
    model.y = pyo.Var(model.T, domain=pyo.Binary)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in types if (i, j) in valid_pairs) >= demand[j - 1]
    model.demand_con = pyo.Constraint(model.T, rule=demand_rule)

    # Link production to fixed cost: if anything produced of type i, y[i] = 1
    def link_rule(m, i):
        return sum(m.x[i, j] for j in types if (i, j) in valid_pairs) <= \
            sum(demand) * m.y[i]
    model.link_con = pyo.Constraint(model.T, rule=link_rule)

    def obj_rule(m):
        return sum(variable_cost[i - 1] * m.x[i, j] for (i, j) in valid_pairs) + \
            sum(fixed_cost * m.y[i] for i in types)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}