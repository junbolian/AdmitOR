import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    n_warehouses = 5
    n_stores = 4
    warehouses = list(range(n_warehouses))
    stores = list(range(n_stores))
    routes = [(i, j) for i in warehouses for j in stores]

    model = pyo.ConcreteModel()

    model.warehouses = pyo.Set(initialize=warehouses)
    model.stores = pyo.Set(initialize=stores)
    model.routes = pyo.Set(initialize=routes, dimen=2)

    model.x = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def supply_rule(m, i):
        return sum(m.x[i, j] for j in m.stores) == supply[i]

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.warehouses) == demand[j]

    model.supply_constraint = pyo.Constraint(model.warehouses, rule=supply_rule)
    model.demand_constraint = pyo.Constraint(model.stores, rule=demand_rule)

    def capacity_rule(m, i, j):
        return m.x[i, j] <= capacity[i][j]

    model.capacity_constraint = pyo.Constraint(model.routes, rule=capacity_rule)

    def objective_rule(m):
        return sum(cost[i][j] * m.x[i, j] for (i, j) in m.routes)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}