import gurobipy as gp
from gurobipy import GRB

def solve(params):
    architect_rankings = params["architect_rankings"]
    engineer_rankings = params["engineer_rankings"]
    w_a = params["friction_cost_architect_rank_weight"]
    w_e = params["friction_cost_engineer_rank_weight"]

    n = len(architect_rankings)  # 7

    # Build rank lookup tables:
    # arch_rank[a][e] = position of engineer e in architect a's ranking (0-indexed)
    # eng_rank[e][a] = position of architect a in engineer e's ranking (0-indexed)
    arch_rank = {}
    for a in range(n):
        arch_rank[a] = {}
        for pos, e in enumerate(architect_rankings[a]):
            arch_rank[a][e] = pos

    eng_rank = {}
    for e in range(n):
        eng_rank[e] = {}
        for pos, a in enumerate(engineer_rankings[e]):
            eng_rank[e][a] = pos

    model = gp.Model("stable_matching")
    model.setParam("OutputFlag", 0)

    # Binary assignment variable: x[a,e] = 1 if architect a is matched with engineer e
    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

    # Perfect matching constraints
    for a in range(n):
        model.addConstr(gp.quicksum(x[a, e] for e in range(n)) == 1, name=f"arch_{a}")
    for e in range(n):
        model.addConstr(gp.quicksum(x[a, e] for a in range(n)) == 1, name=f"eng_{e}")

    # Stability constraints: for every potential blocking pair (a, e),
    # it cannot be that both a prefers e over their current match AND
    # e prefers a over their current match.
    #
    # Blocking pair (a, e) exists iff:
    #   sum_{e' : arch_rank[a][e'] < arch_rank[a][e]} x[a,e'] == 0  (a not matched to someone better)
    #   AND
    #   sum_{a' : eng_rank[e][a'] < eng_rank[e][a]} x[a',e] == 0   (e not matched to someone better)
    #
    # Equivalently, to forbid blocking pair (a,e):
    #   sum_{e': arch_rank[a][e'] <= arch_rank[a][e]} x[a,e']
    #   + sum_{a': eng_rank[e][a'] <= eng_rank[e][a]} x[a',e]  >= 1
    # (at least one of them must be matched to someone at least as good as the other)
    # Note: includes (a,e) itself in both sums, so if they are matched the constraint is trivially satisfied.

    for a in range(n):
        for e in range(n):
            rank_a_e = arch_rank[a][e]
            rank_e_a = eng_rank[e][a]

            # Engineers that a ranks at least as good as e (positions 0..rank_a_e)
            better_or_equal_for_a = [ep for ep in range(n) if arch_rank[a][ep] <= rank_a_e]
            # Architects that e ranks at least as good as a (positions 0..rank_e_a)
            better_or_equal_for_e = [ap for ap in range(n) if eng_rank[e][ap] <= rank_e_a]

            model.addConstr(
                gp.quicksum(x[a, ep] for ep in better_or_equal_for_a)
                + gp.quicksum(x[ap, e] for ap in better_or_equal_for_e)
                >= 1,
                name=f"stable_{a}_{e}"
            )

    # Objective: minimize total weighted friction index
    obj = gp.quicksum(
        (w_a * arch_rank[a][e] + w_e * eng_rank[e][a]) * x[a, e]
        for a in range(n)
        for e in range(n)
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}