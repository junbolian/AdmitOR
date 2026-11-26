import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    # Indices: DCs 1..6, stores 1..9
    num_dcs = len(opening_cost)
    num_stores = len(demand)
    dcs = list(range(1, num_dcs + 1))
    stores = list(range(1, num_stores + 1))

    model = pyo.ConcreteModel()

    model.DC = pyo.Set(initialize=dcs)
    model.STORE = pyo.Set(initialize=stores)
    model.LINK = pyo.Set(dimen=2, initialize=[(i, j) for i in dcs for j in stores])

    # Decision variables
    model.y = pyo.Var(model.DC, domain=pyo.Binary)
    model.x = pyo.Var(model.LINK, domain=pyo.NonNegativeReals)

    # Objective
    def obj_rule(m):
        open_part = sum(opening_cost[i - 1] * m.y[i] for i in m.DC)
        trans_part = sum(transport_cost[i - 1][j - 1] * m.x[i, j] for (i, j) in m.LINK)
        return open_part + trans_part

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Demand satisfaction
    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.DC) == demand[j - 1]

    model.demand_con = pyo.Constraint(model.STORE, rule=demand_rule)

    # Capacity / linking
    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.STORE) <= capacity[i - 1] * m.y[i]

    model.capacity_con = pyo.Constraint(model.DC, rule=capacity_rule)

    solver = Highs()
    solver.solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible or objective not retrievable"}

    return {"objective": obj_val, "status": "optimal"}