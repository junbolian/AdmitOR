import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    upper_limit = params["upper_limit"]
    cost = params["cost"]

    num_persons = len(supply)
    num_projects = len(demand)

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_persons - 1)
    model.J = pyo.RangeSet(0, num_projects - 1)

    def x_bounds(m, i, j):
        return (0, upper_limit[i][j])

    model.x = pyo.Var(model.P, model.J, bounds=x_bounds)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.P for j in m.J)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.J) == supply[i]

    model.supply_con = pyo.Constraint(model.P, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.P) == demand[j]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}