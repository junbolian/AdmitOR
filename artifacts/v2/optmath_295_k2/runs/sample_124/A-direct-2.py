import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    capacity_limits = params["capacity_limits"]
    costs = params["costs"]

    n_people = len(supply)
    n_projects = len(demand)
    people = range(n_people)
    projects = range(n_projects)

    model = pyo.ConcreteModel()

    model.x = pyo.Var(people, projects, domain=pyo.NonNegativeReals)

    def cost_rule(mdl):
        return sum(costs[i][j] * mdl.x[i, j] for i in people for j in projects)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in projects) == supply[i]

    model.supply_constraint = pyo.Constraint(people, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in people) == demand[j]

    model.demand_constraint = pyo.Constraint(projects, rule=demand_rule)

    def cap_rule(mdl, i, j):
        return mdl.x[i, j] <= capacity_limits[i][j]

    model.cap_constraint = pyo.Constraint(people, projects, rule=cap_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.total_cost))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as exc:
        return {"objective": None, "status": "infeasible or failed"}