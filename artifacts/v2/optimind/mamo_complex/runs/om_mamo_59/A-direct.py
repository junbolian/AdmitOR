import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_dc = len(opening_cost)
    n_store = len(demand)
    DC = range(n_dc)
    STORE = range(n_store)

    model = pyo.ConcreteModel()

    model.x_open = pyo.Var(DC, domain=pyo.Binary)
    model.y_flow = pyo.Var(DC, STORE, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        open_term = sum(opening_cost[i] * m.x_open[i] for i in DC)
        flow_term = sum(
            transport_cost[i][j] * m.y_flow[i, j] for i in DC for j in STORE
        )
        return open_term + flow_term

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.y_flow[i, j] for i in DC) == demand[j]

    model.demand_con = pyo.Constraint(STORE, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.y_flow[i, j] for j in STORE) <= capacity[i] * m.x_open[i]

    model.capacity_con = pyo.Constraint(DC, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}