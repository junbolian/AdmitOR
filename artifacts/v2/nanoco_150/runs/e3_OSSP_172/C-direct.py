import gurobipy as gp
from gurobipy import GRB

def solve(params):
    prototypes = ["P0", "P1", "P2"]
    stations = ["S0", "S1", "S2"]

    duration = {}
    for p in prototypes:
        for s in stations:
            duration[(p, s)] = params[f"duration_{p}_{s}"]

    # Big-M for disjunctive constraints
    M = sum(duration[(p, s)] for p in prototypes for s in stations)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # start[p, s] = start time of prototype p on station s
    start = {}
    for p in prototypes:
        for s in stations:
            start[(p, s)] = model.addVar(lb=0.0, name=f"start_{p}_{s}")

    # makespan
    makespan = model.addVar(lb=0.0, name="makespan")

    # y[p1, p2, s] = 1 if p1 precedes p2 on station s
    y = {}
    for s in stations:
        for i, p1 in enumerate(prototypes):
            for j, p2 in enumerate(prototypes):
                if p1 != p2:
                    y[(p1, p2, s)] = model.addVar(vtype=GRB.BINARY, name=f"y_{p1}_{p2}_{s}")

    model.update()

    # Makespan >= completion of every task
    for p in prototypes:
        for s in stations:
            model.addConstr(makespan >= start[(p, s)] + duration[(p, s)])

    # No-overlap on each station: for each pair of prototypes, one must precede the other
    for s in stations:
        for i, p1 in enumerate(prototypes):
            for j, p2 in enumerate(prototypes):
                if p1 != p2:
                    # p1 before p2 OR p2 before p1
                    model.addConstr(
                        start[(p1, s)] + duration[(p1, s)] <= start[(p2, s)] + M * (1 - y[(p1, p2, s)])
                    )

    # Enforce mutual exclusion: exactly one of y[p1,p2,s] or y[p2,p1,s] is 1
    for s in stations:
        for i, p1 in enumerate(prototypes):
            for j, p2 in enumerate(prototypes):
                if i < j:
                    model.addConstr(y[(p1, p2, s)] + y[(p2, p1, s)] == 1)

    # No-overlap per prototype: a prototype can only be at one station at a time
    # z[p, s1, s2] = 1 if task on s1 precedes task on s2 for prototype p
    z = {}
    for p in prototypes:
        for i, s1 in enumerate(stations):
            for j, s2 in enumerate(stations):
                if s1 != s2:
                    z[(p, s1, s2)] = model.addVar(vtype=GRB.BINARY, name=f"z_{p}_{s1}_{s2}")

    model.update()

    for p in prototypes:
        for i, s1 in enumerate(stations):
            for j, s2 in enumerate(stations):
                if s1 != s2:
                    model.addConstr(
                        start[(p, s1)] + duration[(p, s1)] <= start[(p, s2)] + M * (1 - z[(p, s1, s2)])
                    )

    for p in prototypes:
        for i, s1 in enumerate(stations):
            for j, s2 in enumerate(stations):
                if i < j:
                    model.addConstr(z[(p, s1, s2)] + z[(p, s2, s1)] == 1)

    model.setObjective(makespan, GRB.MINIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}