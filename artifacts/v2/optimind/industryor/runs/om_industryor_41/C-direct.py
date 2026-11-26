import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demandA = params["demandA"]
    demandB = params["demandB"]
    demandC = params["demandC"]
    supplyA_A = params["supplyA_A"]
    supplyA_B = params["supplyA_B"]
    supplyA_C = params["supplyA_C"]
    supplyB_A = params["supplyB_A"]
    supplyB_B = params["supplyB_B"]
    supplyB_C = params["supplyB_C"]
    costA = params["costA"]
    costB = params["costB"]

    model = gp.Model("freight_optimization")
    model.setParam("OutputFlag", 0)

    x = model.addVar(vtype=GRB.INTEGER, lb=0, name="trucks_A")
    y = model.addVar(vtype=GRB.INTEGER, lb=0, name="trucks_B")

    model.setObjective(costA * x + costB * y, GRB.MINIMIZE)

    model.addConstr(supplyA_A * x + supplyB_A * y >= demandA, name="demand_rawA")
    model.addConstr(supplyA_B * x + supplyB_B * y >= demandB, name="demand_rawB")
    model.addConstr(supplyA_C * x + supplyB_C * y >= demandC, name="demand_rawC")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}