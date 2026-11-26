import gurobipy as gp
from gurobipy import GRB

def solve(params):
    time0_outflow = params["time0_outflow"]
    time1_outflow = params["time1_outflow"]
    npv = params["npv"]
    budget_time0 = params["budget_time0"]
    budget_time1 = params["budget_time1"]

    n = len(npv)
    investments = range(n)

    model = gp.Model("StarOil")
    model.setParam("OutputFlag", 0)

    x = model.addVars(investments, lb=0.0, ub=1.0, name="x")

    model.setObjective(gp.quicksum(npv[i] * x[i] for i in investments), GRB.MAXIMIZE)

    model.addConstr(
        gp.quicksum(time0_outflow[i] * x[i] for i in investments) <= budget_time0,
        name="budget_t0"
    )
    model.addConstr(
        gp.quicksum(time1_outflow[i] * x[i] for i in investments) <= budget_time1,
        name="budget_t1"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}