import gurobipy as gp
from gurobipy import GRB

def solve(params):
    requirements = params["requirements"]  # list of 7 values: Mon=0 ... Sun=6

    # Decision variables: x[i] = number of employees starting their 5-day shift on day i
    # Days: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    # Employee starting on day i works days i, i+1, i+2, i+3, i+4 (mod 7)

    model = gp.Model("post_office_scheduling")
    model.setParam("OutputFlag", 0)

    # x[i]: number of employees starting on day i (continuous relaxation gives integer here)
    x = model.addVars(7, lb=0, vtype=GRB.CONTINUOUS, name="x")

    # Minimize total employees hired
    model.setObjective(gp.quicksum(x[i] for i in range(7)), GRB.MINIMIZE)

    # Coverage constraints: for each day d, sum of x[i] where day d is in [i, i+1, ..., i+4] mod 7
    # Day d is covered by shift starting on day i if (d - i) mod 7 in {0,1,2,3,4}
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for d in range(7):
        covering = [i for i in range(7) if (d - i) % 7 <= 4]
        model.addConstr(
            gp.quicksum(x[i] for i in covering) >= requirements[d],
            name=f"coverage_{days[d]}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}