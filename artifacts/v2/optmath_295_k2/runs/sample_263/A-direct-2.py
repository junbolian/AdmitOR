import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_origins = len(supply)
    n_dests = len(demand)
    origins = list(range(n_origins))
    dests = list(range(n_dests))

    model = pyo.ConcreteModel()

    model.origins = pyo.Set(initialize=origins)
    model.dests = pyo.Set(initialize=dests)

    model.x = pyo.Var(model.origins, model.dests, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return pyo.summation(m.x, weights={})

    def cost_expr(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.origins for j in m.dests)

    model.total_cost = pyo.Objective(rule=cost_expr, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.dests) == supply[i]

    model.supply_con = pyo.Constraint(model.origins, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.origins) == demand[j]

    model.demand_con = pyo.Constraint(model.dests, rule=demand_rule)

    def cap_rule(m, i, j):
        return m.x[i, j] <= capacity[i][j]

    model.cap_con = pyo.Constraint(model.origins, model.dests, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}