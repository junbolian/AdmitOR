def solve(params):
    import pyomo.environ as pyo
    from pyomo.contrib.appsi.solvers.highs import Highs

    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    centers = list(range(7))
    stores = list(range(7))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(centers, stores, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(centers, domain=pyo.Binary)

    def objective_rule(m):
        return sum(opening_cost[i] * m.y[i] for i in centers) + \
               sum(transport_cost[i][j] * m.x[i, j] for i in centers for j in stores)
    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in centers) == demand[j]
    model.demand_con = pyo.Constraint(stores, rule=demand_rule)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in stores) <= capacity[i] * m.y[i]
    model.capacity_con = pyo.Constraint(centers, rule=capacity_rule)

    solver = Highs()
    solver.solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}