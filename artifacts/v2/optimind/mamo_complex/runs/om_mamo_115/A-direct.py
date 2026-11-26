import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_dc = 7
    n_store = 7
    DC = range(n_dc)
    STORE = range(n_store)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(DC, STORE, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(DC, domain=pyo.Binary)

    def obj_rule(m):
        return sum(opening_cost[i] * m.y[i] for i in DC) + sum(
            transport_cost[i][j] * m.x[i, j] for i in DC for j in STORE
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in DC) == demand[j]

    model.demand_con = pyo.Constraint(STORE, rule=demand_rule)

    def cap_rule(m, i):
        return sum(m.x[i, j] for j in STORE) <= capacity[i] * m.y[i]

    model.cap_con = pyo.Constraint(DC, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}