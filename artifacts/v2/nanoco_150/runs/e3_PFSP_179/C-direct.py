import gurobipy as gp
from gurobipy import GRB
import itertools

def solve(params):
    processing_times = params["processing_times"]
    
    batches = list(range(len(processing_times)))      # 0..3
    stages = list(range(len(processing_times[0])))    # 0..2
    n = len(batches)
    s = len(stages)
    
    # p[i][k] = processing time of batch i at stage k
    p = {i: {k: processing_times[i][k] for k in stages} for i in batches}
    
    # This is a permutation flow shop (no-wait / blocking not stated, so standard
    # flow shop: each machine processes one job at a time, each job one machine at
    # a time, same sequence on all machines).
    # For n=4 we can enumerate all 4! = 24 permutations and pick the best,
    # but we'll use Gurobi MIP for generality.
    #
    # Decision variables:
    #   x[i,j] = 1 if batch i is processed in position j of the sequence
    #   C[i,k] = completion time of batch i at stage k
    #   Cmax   = makespan
    #
    # Let pos[j] = batch assigned to position j.
    # We linearise the precedence via a big-M formulation over positions.

    BIG_M = sum(p[i][k] for i in batches for k in stages) + 1

    model = gp.Model("flowshop")
    model.setParam("OutputFlag", 0)
    model.setParam("TimeLimit", 120)

    # x[i, j] = 1 iff batch i occupies position j
    x = model.addVars(batches, batches, vtype=GRB.BINARY, name="x")

    # C[i, k] = completion time of the batch in position i at stage k
    # (here i is a position index 0..n-1)
    positions = batches  # reuse same index set for positions
    C = model.addVars(positions, stages, vtype=GRB.CONTINUOUS, lb=0.0, name="C")
    Cmax = model.addVar(vtype=GRB.CONTINUOUS, lb=0.0, name="Cmax")

    # Assignment: each batch assigned to exactly one position
    for i in batches:
        model.addConstr(gp.quicksum(x[i, j] for j in positions) == 1, name=f"batch_{i}")
    # Each position filled by exactly one batch
    for j in positions:
        model.addConstr(gp.quicksum(x[i, j] for i in batches) == 1, name=f"pos_{j}")

    # Processing time of position j at stage k (linearised)
    # pt_expr[j, k] = sum_i p[i][k] * x[i, j]
    # We introduce auxiliary variable PT[j,k] = processing time at position j, stage k
    PT = model.addVars(positions, stages, vtype=GRB.CONTINUOUS, lb=0.0, name="PT")
    for j in positions:
        for k in stages:
            model.addConstr(
                PT[j, k] == gp.quicksum(p[i][k] * x[i, j] for i in batches),
                name=f"PT_{j}_{k}"
            )

    # Flow shop completion time constraints:
    # C[j, k] >= C[j, k-1] + PT[j, k]   (same batch, previous stage must finish)
    # C[j, k] >= C[j-1, k] + PT[j, k]   (same stage, previous position must finish)
    # C[0, 0] = PT[0, 0]
    for j in positions:
        for k in stages:
            # Must complete own processing
            if j == 0 and k == 0:
                model.addConstr(C[j, k] >= PT[j, k], name=f"start_{j}_{k}")
            elif j == 0:
                # First position: only depends on previous stage
                model.addConstr(C[j, k] >= C[j, k-1] + PT[j, k], name=f"prev_stage_{j}_{k}")
            elif k == 0:
                # First stage: only depends on previous position
                model.addConstr(C[j, k] >= C[j-1, k] + PT[j, k], name=f"prev_pos_{j}_{k}")
            else:
                model.addConstr(C[j, k] >= C[j, k-1] + PT[j, k], name=f"prev_stage_{j}_{k}")
                model.addConstr(C[j, k] >= C[j-1, k] + PT[j, k], name=f"prev_pos_{j}_{k}")

    # Makespan = completion of last position at last stage
    last_stage = stages[-1]
    last_pos = positions[-1]
    model.addConstr(Cmax >= C[last_pos, last_stage], name="makespan")

    model.setObjective(Cmax, GRB.MINIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL or (model.Status == GRB.TIME_LIMIT and model.SolCount > 0):
        status = "optimal" if model.Status == GRB.OPTIMAL else "time_limit"
        return {"objective": float(model.ObjVal), "status": status}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}