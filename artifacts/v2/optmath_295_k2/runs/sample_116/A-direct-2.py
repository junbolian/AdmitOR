import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    availability = params["consultant_availability"]
    demand = params["project_demand"]
    cost = params["assignment_cost"]
    capacity = params["assignment_capacity"]

    n_consultants = len(availability)
    n_projects = len(demand)

    model = pyo.ConcreteModel()

    model.I = pyo.RangeSet(0, n_consultants - 1)
    model.J = pyo.RangeSet(0, n_projects - 1)

    model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.I for j in m.J)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.J) == availability[i]

    model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.I) == demand[j]

    model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

    def capacity_rule(m, i, j):
        return m.x[i, j] <= capacity[i][j]

    model.capacity_con = pyo.Constraint(model.I, model.J, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}