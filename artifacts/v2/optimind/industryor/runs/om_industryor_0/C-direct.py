import gurobipy as gp
from gurobipy import GRB

def solve(params):
    skilled_workers   = params["skilled_workers"]
    new_workers       = params["new_workers"]
    prod_rate_I       = params["prod_rate_I"]
    prod_rate_II      = params["prod_rate_II"]
    weekly_hours_normal   = params["weekly_hours_normal"]
    weekly_hours_overtime = params["weekly_hours_overtime"]
    train_capacity    = params["train_capacity"]
    train_weeks       = params["train_weeks"]
    wage_skilled      = params["wage_skilled"]
    wage_trainee      = params["wage_trainee"]
    wage_trained      = params["wage_trained"]
    wage_overtime     = params["wage_overtime"]
    penalty_I         = params["penalty_I"]
    penalty_II        = params["penalty_II"]
    demand_I          = params["demand_I"]   # list of length 8
    demand_II         = params["demand_II"]  # list of length 8

    T = 8  # weeks
    weeks = range(T)         # 0..7  (week index, week t+1 = t+1)

    # Training sessions: workers trained in session s become available after week (s + train_weeks)
    # We allow training sessions starting at week 0,1,...,6 (2-week duration means last possible
    # start is week 6 so they finish by end of week 8).
    # Actually train_weeks=2, so a session starting in week w (1-indexed) finishes at end of week w+1.
    # Sessions (0-indexed start week): 0,1,2,3,4,5,6  → finish after week 1,2,3,4,5,6,7 (0-indexed)
    # i.e. available from week 2,3,4,5,6,7,8 (1-indexed) = indices 2,3,4,5,6,7, and 8 is beyond horizon
    # For the new workers constraint: all 50 must be trained by END of week 8,
    # so last session can start week 6 (0-indexed), finishing end of week 7 (0-indexed) = end of week 8.

    # Decision variables:
    # x[t]  = number of skilled workers doing normal production in week t
    # y[t]  = number of skilled/trained workers doing overtime in week t
    # p[t]  = number of skilled workers training trainees, session starting at week t
    #         (session occupies weeks t and t+1, using train_weeks=2)
    # n[t]  = number of trainees in a session starting at week t
    # q[t]  = number of trained (previously trainee) workers in normal production in week t
    # r[t]  = number of trained workers doing overtime in week t
    # s_I[t], s_II[t] = shortage (unmet demand) of food I, II in week t (cumulative shortfall approach)
    # Actually penalty is per kg per week of delay, so we model cumulative undelivered.

    model = gp.Model("factory_training")
    model.setParam("OutputFlag", 0)

    # We track inventory / cumulative surplus to handle delays.
    # Let prod_I[t], prod_II[t] = production in week t.
    # Penalty: for each kg not delivered by week t, pay penalty for each additional week it is late.
    # Equivalent: cumulative_demand[t] - cumulative_production[t] = backlog[t] >= 0
    # Total penalty = sum_t (backlog_I[t] * penalty_I + backlog_II[t] * penalty_II)

    # Training sessions can start at weeks 0..6 (0-indexed), i.e. train_sessions S = {0,1,2,3,4,5,6}
    # But last session starts week 6, trainees available from week 8 (beyond horizon, so they
    # contribute to the "by end of week 8" constraint but don't produce within the 8-week horizon).
    # We allow sessions starting 0..6.
    train_sessions = range(T - train_weeks + 1)  # 0..6

    # Skilled workers available each week = initial - those in training as trainer
    # A trainer in session s is occupied in weeks s and s+1.
    # Trainees in session s are occupied in weeks s and s+1, then become "trained workers" from week s+2.

    # Variables
    # For each week t: skilled normal, skilled overtime
    x = model.addVars(T, lb=0, name="x")   # skilled normal workers producing
    y = model.addVars(T, lb=0, name="y")   # skilled overtime workers

    # For each training session s: p[s]=trainers, n[s]=trainees
    p = model.addVars(len(train_sessions), lb=0, name="p")   # trainers in session s
    n = model.addVars(len(train_sessions), lb=0, name="n")   # trainees in session s

    # For each week t: trained workers (from previous sessions) in normal or overtime
    q = model.addVars(T, lb=0, name="q")   # trained normal
    r_ov = model.addVars(T, lb=0, name="r_ov")  # trained overtime

    # Allocation of production between food I and II
    # Hours available per worker: normal=weekly_hours_normal, overtime=weekly_hours_overtime
    # Let hI_x[t] = hours skilled-normal workers spend on food I
    # Let hII_x[t] = hours skilled-normal workers spend on food II
    hI_x  = model.addVars(T, lb=0, name="hI_x")
    hII_x = model.addVars(T, lb=0, name="hII_x")
    hI_y  = model.addVars(T, lb=0, name="hI_y")
    hII_y = model.addVars(T, lb=0, name="hII_y")
    hI_q  = model.addVars(T, lb=0, name="hI_q")
    hII_q = model.addVars(T, lb=0, name="hII_q")
    hI_r  = model.addVars(T, lb=0, name="hI_r")
    hII_r = model.addVars(T, lb=0, name="hII_r")

    # Production each week
    # prod_I[t] = prod_rate_I * (hI_x[t] + hI_y[t] + hI_q[t] + hI_r[t])
    # prod_II[t] = prod_rate_II * (hII_x[t] + hII_y[t] + hII_q[t] + hII_r[t])

    # Backlog variables
    bl_I  = model.addVars(T, lb=0, name="bl_I")
    bl_II = model.addVars(T, lb=0, name="bl_II")

    # --- Constraints ---

    # Number of trained workers available at week t = sum of trainees from sessions that finished before t
    # Session s finishes after week s + train_weeks - 1 (0-indexed), available from week s + train_weeks
    def trained_available(t):
        return gp.quicksum(n[s] for s in train_sessions if s + train_weeks <= t)

    # Number of skilled workers being trained (as trainers) at week t
    def trainers_at(t):
        return gp.quicksum(p[s] for s in train_sessions if s <= t < s + train_weeks)

    # Number of trainees at week t
    def trainees_at(t):
        return gp.quicksum(n[s] for s in train_sessions if s <= t < s + train_weeks)

    for t in weeks:
        skilled_avail = skilled_workers  # initial skilled workers

        # Skilled workers balance: x[t] + y[t] + trainers_at(t) <= skilled_avail
        # (trained workers after their session are like skilled workers for production)
        model.addConstr(
            x[t] + y[t] + trainers_at(t) <= skilled_avail,
            name=f"skilled_bal_{t}"
        )

        # Trained workers balance: q[t] + r_ov[t] <= trained_available(t)
        model.addConstr(
            q[t] + r_ov[t] <= trained_available(t),
            name=f"trained_bal_{t}"
        )

        # Hours constraints for skilled normal workers
        model.addConstr(hI_x[t] + hII_x[t] == x[t] * weekly_hours_normal,
                        name=f"hours_x_{t}")
        # Hours for skilled overtime
        model.addConstr(hI_y[t] + hII_y[t] == y[t] * weekly_hours_overtime,
                        name=f"hours_y_{t}")
        # Hours for trained normal
        model.addConstr(hI_q[t] + hII_q[t] == q[t] * weekly_hours_normal,
                        name=f"hours_q_{t}")
        # Hours for trained overtime
        model.addConstr(hI_r[t] + hII_r[t] == r_ov[t] * weekly_hours_overtime,
                        name=f"hours_r_{t}")

    # Trainee capacity: trainees per trainer per session
    for s in train_sessions:
        model.addConstr(n[s] <= train_capacity * p[s], name=f"train_cap_{s}")

    # Total new workers trained by end of week 8
    model.addConstr(
        gp.quicksum(n[s] for s in train_sessions) >= new_workers,
        name="new_workers_total"
    )

    # Backlog constraints (cumulative demand - cumulative production = backlog)
    for t in weeks:
        cum_demand_I  = sum(demand_I[tau]  for tau in range(t + 1))
        cum_demand_II = sum(demand_II[tau] for tau in range(t + 1))

        cum_prod_I  = gp.quicksum(
            prod_rate_I * (hI_x[tau] + hI_y[tau] + hI_q[tau] + hI_r[tau])
            for tau in range(t + 1)
        )
        cum_prod_II = gp.quicksum(
            prod_rate_II * (hII_x[tau] + hII_y[tau] + hII_q[tau] + hII_r[tau])
            for tau in range(t + 1)
        )

        model.addConstr(bl_I[t]  >= cum_demand_I  - cum_prod_I,  name=f"backlog_I_{t}")
        model.addConstr(bl_II[t] >= cum_demand_II - cum_prod_II, name=f"backlog_II_{t}")

    # --- Objective ---
    # Wage costs
    wage_cost = gp.LinExpr()
    for t in weeks:
        # Skilled normal workers
        wage_cost += wage_skilled * x[t]
        # Skilled overtime workers
        wage_cost += wage_overtime * y[t]
        # Trainers (also paid as skilled workers during training)
        wage_cost += wage_skilled * trainers_at(t)
        # Trainees during training
        wage_cost += wage_trainee * trainees_at(t)
        # Trained workers (normal)
        wage_cost += wage_trained * q[t]
        # Trained workers (overtime)
        wage_cost += wage_overtime * r_ov[t]

    # Penalty costs
    penalty_cost = gp.quicksum(
        penalty_I * bl_I[t] + penalty_II * bl_II[t] for t in weeks
    )

    model.setObjective(wage_cost + penalty_cost, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}