import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    costs = params["costs"]
    supply = params["supply"]
    demand = params["demand"]
    capacity_limits = params["capacity_limits"]

    model = pyo.ConcreteModel()

    persons = list(range(len(supply)))
    projects = list(range(len(demand)))

    model.x = pyo.Var(persons, projects, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(costs[i][j] * m.x[i, j] for i in persons for j in projects)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in projects) == supply[i]
    model.supply_con = pyo.Constraint(persons, rule=supply_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in persons) == demand[j]
    model.demand_con = pyo.Constraint(projects, rule=demand_rule)

    def cap_rule(m, i, j):
        return m.x[i, j] <= capacity_limits[i][j]
    model.cap_con = pyo.Constraint(persons, projects, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}