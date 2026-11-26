import gurobipy as gp
from gurobipy import GRB

def solve(params):
    a = params["a_j"]
    k = params["k"]
    n = len(a)

    # Cumulative jets available by year j (1-indexed, so index j-1 in 0-indexed)
    S = []
    running = 0
    for j in range(n):
        running += a[j]
        S.append(running)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[j] = jets allocated to training in year j (0-indexed)
    x = model.addVars(n, lb=0.0, name="x")

    # x[j] <= S[j]: can't allocate more training jets than available
    for j in range(n):
        model.addConstr(x[j] <= S[j], name=f"cap_{j}")

    # Pilot constraint: combat jets in year j = S[j] - x[j]
    # Pilots available at start of year j = k * sum(x[i] for i < j)
    # For j=0: no prior training, so combat jets must be 0 (or pilots=0 means no combat)
    # S[j] - x[j] <= k * sum(x[i] for i in range(j))
    for j in range(n):
        prior_pilots = gp.quicksum(k * x[i] for i in range(j))
        # For j=0, prior_pilots = 0, so S[0] - x[0] <= 0 => x[0] = S[0]
        model.addConstr(S[j] - x[j] <= prior_pilots, name=f"pilot_{j}")

    # Objective: maximize total combat jet-years
    model.setObjective(
        gp.quicksum(S[j] - x[j] for j in range(n)),
        GRB.MAXIMIZE
    )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}