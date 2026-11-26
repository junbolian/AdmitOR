import gurobipy as gp
from gurobipy import GRB

def solve(params):
    d = [params["demand_2_6"], params["demand_6_10"], params["demand_10_14"],
         params["demand_14_18"], params["demand_18_22"], params["demand_22_2"]]
    sr = params["salary_regular"]
    sc = params["salary_contract"]
    L = params["shift_length"]
    n = 6  # number of 4-hour periods / start batches

    model = gp.Model("nurses")
    model.Params.OutputFlag = 0

    reg = model.addVars(n, lb=0, vtype=GRB.INTEGER, name="reg")
    con = model.addVars(n, lb=0, vtype=GRB.INTEGER, name="con")

    # Each period i is covered by nurses starting at batch i and batch (i-1) % n
    # because shift_length covers 2 consecutive 4-hour periods
    for i in range(n):
        prev = (i - 1) % n
        model.addConstr(
            reg[i] + con[i] + reg[prev] + con[prev] >= d[i],
            name=f"demand_{i}"
        )

    model.setObjective(
        gp.quicksum((sr * L) * reg[i] + (sc * L) * con[i] for i in range(n)),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status != GRB.OPTIMAL:
        return {"objective": None, "status": f"status_{model.Status}"}

    return {"objective": float(model.ObjVal), "status": "optimal"}