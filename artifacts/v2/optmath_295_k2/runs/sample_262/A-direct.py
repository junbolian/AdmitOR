import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    ship_cost = params["ship_cost"]
    capacity = params["capacity"]

    n_fac = len(fixed_cost)
    n_cus = len(demand)
    facilities = list(range(n_fac))
    customers = list(range(n_cus))

    model = pyo.ConcreteModel()

    model.FAC = pyo.Set(initialize=facilities)
    model.CUS = pyo.Set(initialize=customers)
    model.FC = pyo.Set(initialize=[(i, j) for i in facilities for j in customers], dimen=2)

    model.y = pyo.Var(model.FAC, domain=pyo.Binary)
    model.x = pyo.Var(model.FC, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(fixed_cost[i] * m.y[i] for i in m.FAC) + \
               sum(ship_cost[i][j] * m.x[i, j] for (i, j) in m.FC)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.FAC) == demand[j]

    model.demand_con = pyo.Constraint(model.CUS, rule=demand_rule)

    def cap_rule(m, i):
        return sum(m.x[i, j] for j in m.CUS) <= capacity[i] * m.y[i]

    model.cap_con = pyo.Constraint(model.FAC, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}