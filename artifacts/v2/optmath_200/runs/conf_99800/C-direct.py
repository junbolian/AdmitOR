import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    
    num_peaks = len(cost_matrix)
    num_amino_acids = len(cost_matrix[0])
    
    model = gp.Model()
    model.setParam("OutputFlag", 0)
    
    x = model.addVars(num_peaks, num_amino_acids, vtype=GRB.BINARY, name="x")
    
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in range(num_peaks) for j in range(num_amino_acids)),
        GRB.MINIMIZE
    )
    
    for i in range(num_peaks):
        model.addConstr(gp.quicksum(x[i, j] for j in range(num_amino_acids)) <= 1, name=f"peak_{i}")
    
    for j in range(num_amino_acids):
        model.addConstr(gp.quicksum(x[i, j] for i in range(num_peaks)) <= 1, name=f"amino_{j}")
    
    model.addConstr(
        gp.quicksum(x[i, j] for i in range(num_peaks) for j in range(num_amino_acids)) == 2,
        name="total_assignments"
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