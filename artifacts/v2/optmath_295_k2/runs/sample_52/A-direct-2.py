import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    capacity = params["capacity"]
    variable_cost = params["variable_cost"]

    n_fac = len(fixed_cost)
    n_cust = len(demand)
    facs = range(n_fac)
    custs = range(n_cust)

    model = pyo.ConcreteModel()

    model.FAC = pyo.Set(initialize=list(facs))
    model.CUST = pyo.Set(initialize=list(custs))

    model.x = pyo.Var(model.FAC, model.CUST, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.FAC, domain=pyo.Binary)

    def obj_rule(m):
        return sum(fixed_cost[f] * m.y[f] for f in m.FAC) + sum(
            variable_cost[f][c] * m.x[f, c] for f in m.FAC for c in m.CUST
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, c):
        return sum(m.x[f, c] for f in m.FAC) == demand[c]

    model.demand_con = pyo.Constraint(model.CUST, rule=demand_rule)

    def capacity_rule(m, f):
        return sum(m.x[f, c] for c in m.CUST) <= capacity[f] * m.y[f]

    model.capacity_con = pyo.Constraint(model.FAC, rule=capacity_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}