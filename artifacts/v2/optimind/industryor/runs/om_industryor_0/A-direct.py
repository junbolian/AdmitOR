import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    skilled = int(params["skilled_workers"])
    new_workers = int(params["new_workers"])
    rate_I = params["prod_rate_I"]
    rate_II = params["prod_rate_II"]
    h_normal = params["weekly_hours_normal"]
    h_overtime = params["weekly_hours_overtime"]
    train_cap = params["train_capacity"]
    train_weeks = int(params["train_weeks"])
    w_skilled = params["wage_skilled"]
    w_trainee = params["wage_trainee"]
    w_trained = params["wage_trained"]
    w_ot = params["wage_overtime"]
    pen_I = params["penalty_I"]
    pen_II = params["penalty_II"]
    demand_I = params["demand_I"]
    demand_II = params["demand_II"]

    T = 8
    weeks = list(range(1, T + 1))
    foods = ["I", "II"]

    model = pyo.ConcreteModel()
    model.W = pyo.Set(initialize=weeks)
    model.F = pyo.Set(initialize=foods)

    # Training start weeks: training lasts train_weeks, done by end of week T
    max_start = T - train_weeks + 1
    train_start_weeks = list(range(1, max_start + 1))

    # x[w]: number of skilled workers starting training at week w
    model.x = pyo.Var(train_start_weeks, domain=pyo.NonNegativeReals)

    # overtime skilled workers each week
    model.o = pyo.Var(model.W, domain=pyo.NonNegativeReals)

    # production of each food each week
    model.prod = pyo.Var(model.F, model.W, domain=pyo.NonNegativeReals)

    # backlog (undelivered demand) per food per week
    model.backlog = pyo.Var(model.F, model.W, domain=pyo.NonNegativeReals)

    # number of trained workers active in week w
    def trained_w(w):
        total = 0
        for s in train_start_weeks:
            if s + train_weeks <= w:
                total = total + model.x[s] * train_cap
        return total

    # number of skilled workers in training (absent) in week w
    def in_training(w):
        total = 0
        for s in train_start_weeks:
            if s <= w <= s + train_weeks - 1:
                total = total + model.x[s]
        return total

    # skiled workers available for production (non-overtime) and overtime
    def skilled_prod(w):
        return skilled - in_training(w)

    # Capacity: production hours constraint per food per week
    def prod_cap_rule(mdl, f, w):
        avail = (skilled_prod(w) + trained_w(w)) * h_normal + mdl.o[w] * (h_overtime - h_normal)
        if f == "I":
            return mdl.prod[f, w] <= avail * rate_I
        return mdl.prod[f, w] <= avail * rate_II

    model.prod_cap = pyo.Constraint(model.F, model.W, rule=prod_cap_rule)

    # Backlog balance
    def backlog_rule(mdl, f, w):
        d = demand_I[w - 1] if f == "I" else demand_II[w - 1]
        if w == 1:
            return mdl.backlog[f, w] == d - mdl.prod[f, w]
        return mdl.backlog[f, w] == mdl.backlog[f, w - 1] + d - mdl.prod[f, w]

    model.backlog_con = pyo.Constraint(model.F, model.W, rule=backlog_rule)

    # Final backlog must be zero (all demand delivered by week 8)
    def final_rule(mdl, f):
        return mdl.backlog[f, T] == 0

    model.final_con = pyo.Constraint(model.F, rule=final_rule)

    # Overtime workers cannot exceed available skilled production workers
    def ot_rule(mdl, w):
        return mdl.o[w] <= skilled_prod(w)

    model.ot_con = pyo.Constraint(model.W, rule=ot_rule)

    # Total new workers trained = new_workers
    def new_total_rule(mdl):
        return sum(mdl.x[s] * train_cap for s in train_start_weeks) == new_workers

    model.new_total_con = pyo.Constraint(rule=new_total_rule)

    # Objective
    def wage_rule(mdl):
        total = 0
        for w in weeks:
            # skilled workers not in training get normal wage
            total = total + (skilled - in_training(w)) * w_skilled
            # trainees (during training) get trainee wage
            total = total + in_training(w) * w_trainee
            # trained workers get trained wage
            total = total + trained_w(w) * w_trained
            # overtime workers get overtime wage
            total = total + mdl.o[w] * w_ot
        return total

    def penalty_rule(mdl):
        total = 0
        for f in foods:
            p = pen_I if f == "I" else pen_II
            for w in weeks:
                total = total + p * mdl.backlog[f, w]
        return total

    model.wage_expr = pyo.Expression(rule=wage_rule)
    model.penalty_expr = pyo.Expression(rule=penalty_rule)

    model.obj = pyo.Objective(
        expr=model.wage_expr + model.penalty_expr, sense=pyo.minimize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}