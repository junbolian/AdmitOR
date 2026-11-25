import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    capacity = params["capacity"]
    leg_utilization = params["leg_utilization"]

    n_pkg = len(revenue)
    n_leg = len(capacity)

    model = pyo.ConcreteModel()

    model.PKG = pyo.RangeSet(0, n_pkg - 1)
    model.LEG = pyo.RangeSet(0, n_leg - 1)

    model.x = pyo.Var(model.PKG, domain=pyo.NonNegativeIntegers)

    def demand_rule(m, j):
        return m.x[j] <= demand[j]

    model.demand_con = pyo.Constraint(model.PKG, rule=demand_rule)

    def cap_rule(m, i):
        return sum(leg_utilization[i][j] * m.x[j] for j in range(n_pkg)) <= capacity[i]

    model.cap_con = pyo.Constraint(model.LEG, rule=cap_rule)

    def obj_rule(m):
        return sum(revenue[j] * m.x[j] for j in range(n_pkg))

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}