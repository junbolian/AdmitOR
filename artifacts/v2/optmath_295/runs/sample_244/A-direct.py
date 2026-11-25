import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    ship_cost = params["ship_cost"]

    n_fac = len(fixed_cost)
    n_cust = len(demand)

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, n_fac - 1)
    model.C = pyo.RangeSet(0, n_cust - 1)
    model.FC = pyo.Set(initialize=[(i, j) for i in range(n_fac) for j in range(n_cust)])

    model.open_fac = pyo.Var(model.F, domain=pyo.Binary)
    model.ship = pyo.Var(model.FC, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(fixed_cost[i] * m.open_fac[i] for i in m.F) + \
               sum(ship_cost[i][j] * m.ship[i, j] for (i, j) in m.FC)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.ship[i, j] for i in m.F) == demand[j]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def cap_rule(m, i):
        return sum(m.ship[i, j] for j in m.C) <= capacity[i] * m.open_fac[i]

    model.cap_con = pyo.Constraint(model.F, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}