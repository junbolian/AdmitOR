def solve(params):
    import pyomo.environ as pyo
    from pyomo.contrib.appsi.solvers.highs import Highs

    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    centers = list(range(9))
    stores = list(range(5))

    model = pyo.ConcreteModel()

    # Decision variables
    model.y = pyo.Var(centers, domain=pyo.Binary)          # open center
    model.x = pyo.Var(centers, stores, domain=pyo.NonNegativeReals)  # flow

    # Objective: opening costs + transportation costs
    model.total_cost = pyo.Objective(
        expr=sum(opening_cost[i] * model.y[i] for i in centers)
        + sum(transport_cost[i][j] * model.x[i, j]
              for i in centers for j in stores),
        sense=pyo.minimize,
    )

    # Demand satisfaction
    model.demand_con = pyo.Constraint(
        stores,
        rule=lambda mdl, j: sum(mdl.x[i, j] for i in centers) == demand[j],
    )

    # Capacity / linkage constraints
    model.capacity_con = pyo.Constraint(
        centers,
        rule=lambda mdl, i: sum(mdl.x[i, j] for j in stores)
        <= capacity[i] * mdl.y[i],
    )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}