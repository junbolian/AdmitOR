import gurobipy as gp
from gurobipy import GRB

def solve(params):
    strategy_costs = params["strategy_costs"]

    # Coverage: segment index (0-based) -> list of strategy indices (0-based)
    coverage = [
        [0, 1, 2, 3, 6],        # Segment 1
        [0, 2, 4, 5, 6, 7],     # Segment 2
        [1, 2, 3, 4, 6],        # Segment 3
        [4, 5],                  # Segment 4
        [1, 2, 4, 6, 7],        # Segment 5
        [2, 5, 6, 7],           # Segment 6
        [6],                     # Segment 7
        [3, 7],                  # Segment 8
        [1, 2, 5, 7],           # Segment 9
        [1, 3, 6],              # Segment 10
        [4, 5],                  # Segment 11
        [0, 1, 3, 6],           # Segment 12
        [1, 2, 3, 5, 7],        # Segment 13
        [0, 1, 2, 6],           # Segment 14
        [4, 5],                  # Segment 15
        [0, 1, 2, 4, 5, 6, 7],  # Segment 16
        [6],                     # Segment 17
        [0, 3, 5],              # Segment 18
        [1, 4, 6],              # Segment 19
        [2, 5],                  # Segment 20
        [0, 3, 4, 5],           # Segment 21
        [1, 4, 5, 7],           # Segment 22
        [0, 7],                  # Segment 23
        [3, 4, 5, 7],           # Segment 24
        [0],                     # Segment 25
        [0, 1, 3, 7],           # Segment 26
        [6],                     # Segment 27
        [1, 3],                  # Segment 28
        [0, 1, 3, 5],           # Segment 29
        [6, 7],                  # Segment 30
        [2, 3],                  # Segment 31
        [4, 7],                  # Segment 32
        [3, 5],                  # Segment 33
        [2, 4, 6],              # Segment 34
        [2, 4, 5],              # Segment 35
        [0, 2, 3, 4],           # Segment 36
        [1],                     # Segment 37
        [0, 1, 5],              # Segment 38
        [0, 1, 2, 3, 6, 7],    # Segment 39
    ]

    n_strategies = 8

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_strategies, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(strategy_costs[s] * x[s] for s in range(n_strategies)),
        GRB.MINIMIZE
    )

    for seg_idx, strategies in enumerate(coverage):
        model.addConstr(
            gp.quicksum(x[s] for s in strategies) >= 1,
            name=f"seg_{seg_idx + 1}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}