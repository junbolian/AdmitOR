import gurobipy as gp
from gurobipy import GRB


def solve(params):
    profit = params["profit"]
    stage_capacity = params["stage_capacity"]
    stage_time = params["stage_time"]
    min_production = params["min_production"]
    max_demand = params["max_demand"]

    num_products = len(profit)
    num_stages = len(stage_capacity)

    model = gp.Model("production_planning")
    model.Params.OutputFlag = 0

    x = model.addVars(
        num_products,
        lb=[float(min_production[i]) for i in range(num_products)],
        ub=[float(max_demand[i]) for i in range(num_products)],
        vtype=GRB.CONTINUOUS,
        name="x",
    )

    model.setObjective(
        gp.quicksum(float(profit[i]) * x[i] for i in range(num_products)),
        GRB.MAXIMIZE,
    )

    for s in range(num_stages):
        # stage_time may be a 2D list (row per stage) or a flat list
        row = stage_time[s] if hasattr(stage_time[s], "__len__") else [
            stage_time[s * num_products + i] for i in range(num_products)
        ]
        model.addConstr(
            gp.quicksum(float(row[i]) * x[i] for i in range(num_products))
            <= float(stage_capacity[s]),
            name=f"stage_{s}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}