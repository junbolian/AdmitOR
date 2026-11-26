import gurobipy as gp
from gurobipy import GRB

def solve(params):
    prod_rate_I = params["prod_rate_I"]
    prod_rate_II = params["prod_rate_II"]
    initial_skilled_workers = params["initial_skilled_workers"]
    target_new_workers = params["target_new_workers"]
    weekly_hours_normal = params["weekly_hours_normal"]
    weekly_hours_overtime = params["weekly_hours_overtime"]
    max_trainees_per_trainer = params["max_trainees_per_trainer"]
    training_duration_weeks = params["training_duration_weeks"]
    salary_skilled_weekly = params["salary_skilled_weekly"]
    salary_trainee_training_weekly = params["salary_trainee_training_weekly"]
    salary_trainee_after_weekly = params["salary_trainee_after_weekly"]
    salary_overtime_weekly = params["salary_overtime_weekly"]
    penalty_shortage_I = params["penalty_shortage_I"]
    penalty_shortage_II = params["penalty_shortage_II"]
    demand_I = params["demand_I"]    # list of 8 values (kg)
    demand_II = params["demand_II"]  # list of 8 values (kg)

    # Number of weeks
    T = 8
    weeks = range(T)  # 0..7 representing weeks 1..8

    # Training batches: training lasts training_duration_weeks (2 weeks)
    # Batches can start at the beginning of weeks 1,3,5,7 (0-indexed: 0,2,4,6)
    # A batch starting at week t (0-indexed) trains during weeks t and t+1,
    # and workers are available from week t+2 onward.
    # Possible start weeks (0-indexed): 0, 2, 4, 6
    batch_starts = [0, 2, 4, 6]  # 0-indexed week indices where a batch can start

    model = gp.Model("factory_scheduling")
    model.setParam("OutputFlag", 0)

    # Decision variables:
    # n[b]: number of trainees in batch b (batch starts at week batch_starts[b])
    n = {}
    for b, bs in enumerate(batch_starts):
        n[b] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"n_{b}")

    # trainer[b]: number of skilled workers assigned as trainers in batch b
    trainer = {}
    for b, bs in enumerate(batch_starts):
        trainer[b] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"trainer_{b}")

    # For each week t (0-indexed), for each food type:
    # x_I[t]: number of normal-hour workers producing food I in week t
    # x_II[t]: number of normal-hour workers producing food II in week t
    # o_I[t]: number of overtime workers producing food I in week t
    # o_II[t]: number of overtime workers producing food II in week t
    x_I = {}
    x_II = {}
    o_I = {}
    o_II = {}
    for t in weeks:
        x_I[t] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"xI_{t}")
        x_II[t] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"xII_{t}")
        o_I[t] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"oI_{t}")
        o_II[t] = model.addVar(lb=0, vtype=GRB.INTEGER, name=f"oII_{t}")

    # Shortage variables
    short_I = {}
    short_II = {}
    for t in weeks:
        short_I[t] = model.addVar(lb=0, name=f"shortI_{t}")
        short_II[t] = model.addVar(lb=0, name=f"shortII_{t}")

    # Constraints

    # 1. Total new workers trained = target_new_workers
    model.addConstr(gp.quicksum(n[b] for b in range(len(batch_starts))) == target_new_workers,
                    name="total_trainees")

    # 2. Trainer capacity: trainers for batch b can train at most max_trainees_per_trainer each
    for b in range(len(batch_starts)):
        model.addConstr(n[b] <= max_trainees_per_trainer * trainer[b],
                        name=f"trainer_cap_{b}")

    # 3. Available skilled workers for production in each week
    # In week t (0-indexed):
    # - Initial skilled workers = initial_skilled_workers
    # - Graduated workers from batches that finished before week t:
    #   batch b finishes at week batch_starts[b] + training_duration_weeks
    #   so available from week batch_starts[b] + training_duration_weeks onward
    # - Workers assigned as trainers in batches active during week t cannot produce
    #   A batch b is active during weeks batch_starts[b] and batch_starts[b]+1

    for t in weeks:
        # Skilled workers: initial + graduated
        skilled_available = initial_skilled_workers
        for b, bs in enumerate(batch_starts):
            grad_week = bs + training_duration_weeks  # week index when they become available
            if t >= grad_week:
                skilled_available = skilled_available + n[b]

        # Trainers occupied in week t (from active batches)
        trainers_busy = gp.LinExpr()
        for b, bs in enumerate(batch_starts):
            if bs <= t < bs + training_duration_weeks:
                trainers_busy += trainer[b]

        # Total productive workers in week t (normal + overtime)
        # Normal workers: x_I[t] + x_II[t]
        # Overtime workers: o_I[t] + o_II[t]
        # All productive workers come from available skilled (including graduated) minus trainers
        # Note: overtime workers are a subset of the productive workers (they work more hours)
        # We model: total workers assigned to production = x_I[t] + x_II[t] (normal)
        #           plus o_I[t] + o_II[t] (overtime)
        # These must not exceed available_productive workers

        # Trainees during training do not produce, so only count graduated ones
        # Trainers don't produce during their training weeks
        model.addConstr(
            x_I[t] + x_II[t] + o_I[t] + o_II[t] <= skilled_available - trainers_busy,
            name=f"worker_cap_{t}"
        )

        # Also trainers must not exceed skilled_available at that time
        # (trainers must be skilled workers available at start of batch)

    # 4. Trainer availability: trainers for batch b must be from initial skilled workers
    #    (since batches can overlap, sum of concurrent trainers <= initial_skilled)
    #    More precisely, at any week, total trainers busy + production workers <= available skilled
    #    Already handled above. But we need trainer[b] to come from available skilled at batch start.
    for b, bs in enumerate(batch_starts):
        # At week bs, the skilled workers available = initial + graduated before bs
        skilled_at_start = initial_skilled_workers
        for b2, bs2 in enumerate(batch_starts):
            if bs2 + training_duration_weeks <= bs:
                skilled_at_start = skilled_at_start + n[b2]
        # trainer[b] <= skilled_at_start (but skilled_at_start may contain n variables)
        # This is implicitly handled by the weekly worker capacity constraint
        # Add explicit constraint that trainers <= available skilled at that time
        model.addConstr(trainer[b] <= skilled_at_start, name=f"trainer_avail_{b}")

    # 5. Supply/demand with shortages
    for t in weeks:
        prod_I = (x_I[t] * weekly_hours_normal + o_I[t] * weekly_hours_overtime) * prod_rate_I
        prod_II = (x_II[t] * weekly_hours_normal + o_II[t] * weekly_hours_overtime) * prod_rate_II

        model.addConstr(prod_I + short_I[t] >= demand_I[t], name=f"demand_I_{t}")
        model.addConstr(prod_II + short_II[t] >= demand_II[t], name=f"demand_II_{t}")

    # 6. Objective: minimize total cost
    # Cost components:
    # a) Salary for skilled workers (not training): salary_skilled_weekly per week
    # b) Salary for overtime skilled workers: salary_overtime_weekly (instead of salary_skilled_weekly)
    #    So extra cost for overtime = salary_overtime_weekly - salary_skilled_weekly per overtime worker
    # c) Trainers: salary_skilled_weekly
    # d) Trainees during training: salary_trainee_training_weekly
    # e) Graduated trainees after training: salary_trainee_after_weekly
    # f) Penalty for shortages

    # We pay ALL skilled workers (including trainers) their base salary each week.
    # Overtime workers get salary_overtime_weekly instead of salary_skilled_weekly.
    # So total salary cost per week t:
    #   - All available skilled workers (not in training as trainers, not overtime): salary_skilled_weekly
    #   - Trainers: salary_skilled_weekly
    #   - Overtime workers: salary_overtime_weekly (they replace normal salary)
    #   - Trainees in training: salary_trainee_training_weekly
    #   - Graduated trainees: salary_trainee_after_weekly

    # Simpler approach: 
    # Total workers available in week t = initial_skilled + graduated_by_t
    # They all get salary_skilled_weekly EXCEPT:
    #   - overtime workers get salary_overtime_weekly
    # So cost = (available - overtime_workers)*salary_skilled + overtime_workers*salary_overtime
    #         + trainees_in_training * salary_trainee_training
    #         + graduated_trainees * salary_trainee_after

    cost = gp.LinExpr()

    for t in weeks:
        # Available skilled workers (initial + graduated)
        skilled_base = initial_skilled_workers
        for b, bs in enumerate(batch_starts):
            grad_week = bs + training_duration_weeks
            if t >= grad_week:
                skilled_base = skilled_base + n[b]

        overtime_workers = o_I[t] + o_II[t]

        # Skilled worker salary: 
        # (skilled_base - overtime_workers) * salary_skilled + overtime_workers * salary_overtime
        # = skilled_base * salary_skilled + overtime_workers * (salary_overtime - salary_skilled)
        cost += skilled_base * salary_skilled_weekly
        cost += overtime_workers * (salary_overtime_weekly - salary_skilled_weekly)

        # Trainees in training during week t
        for b, bs in enumerate(batch_starts):
            if bs <= t < bs + training_duration_weeks:
                cost += n[b] * salary_trainee_training_weekly

        # Graduated trainees in week t
        for b, bs in enumerate(batch_starts):
            grad_week = bs + training_duration_weeks
            if t >= grad_week:
                cost += n[b] * salary_trainee_after_weekly

        # Penalties
        cost += short_I[t] * penalty_shortage_I
        cost += short_II[t] * penalty_shortage_II

    model.setObjective(cost, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}