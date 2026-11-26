import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # ---- Read parameters ----
    rate_I = params["prod_rate_I"]
    rate_II = params["prod_rate_II"]
    init_skilled = params["initial_skilled_workers"]
    target_new = params["target_new_workers"]
    hours_normal = params["weekly_hours_normal"]
    hours_overtime = params["weekly_hours_overtime"]
    max_trainees = params["max_trainees_per_trainer"]
    train_weeks = params["training_duration_weeks"]
    sal_skilled = params["salary_skilled_weekly"]
    sal_trainee_train = params["salary_trainee_training_weekly"]
    sal_trainee_after = params["salary_trainee_after_weekly"]
    sal_overtime = params["salary_overtime_weekly"]
    pen_I = params["penalty_shortage_I"]
    pen_II = params["penalty_shortage_II"]
    dem_I = params["demand_I"]
    dem_II = params["demand_II"]

    weeks = list(range(1, 9))
    n_train_weeks = int(train_weeks)

    model = pyo.ConcreteModel()

    # ---- Variables ----
    # Number of skilled workers assigned as trainers in training block starting at week t
    model.trainers = pyo.Var(weeks, within=pyo.NonNegativeIntegers)
    # Number of trainees in training block starting at week t
    model.trainees = pyo.Var(weeks, within=pyo.NonNegativeIntegers)
    # Skilled workers working overtime (60h) / normally (40h) in production in week w
    model.prod_skilled_overtime = pyo.Var(weeks, within=pyo.NonNegativeIntegers)
    model.prod_skilled_normal = pyo.Var(weeks, within=pyo.NonNegativeIntegers)
    # Trained workers (now skilled) working overtime / normally in production in week w
    model.prod_trained_normal = pyo.Var(weeks, within=pyo.NonNegativeIntegers)
    model.prod_trained_overtime = pyo.Var(weeks, within=pyo.NonNegativeIntegers)
    # Production amounts and shortages
    model.prod_food_I = pyo.Var(weeks, within=pyo.NonNegativeReals)
    model.prod_food_II = pyo.Var(weeks, within=pyo.NonNegativeReals)
    model.shortage_I = pyo.Var(weeks, within=pyo.NonNegativeReals)
    model.shortage_II = pyo.Var(weeks, within=pyo.NonNegativeReals)

    # ---- Constraints ----
    # Trainee capacity per trainer
    model.trainer_capacity = pyo.Constraint(
        weeks, rule=lambda m, w: m.trainees[w] <= max_trainees * m.trainers[w]
    )

    # Training blocks must fit in horizon
    model.training_fit = pyo.ConstraintList()
    for w in weeks:
        if w + n_train_weeks > 8:
            model.training_fit.add(model.trainees[w] == 0)
            model.training_fit.add(model.trainers[w] == 0)

    # Must train target number of new workers
    model.target_constraint = pyo.Constraint(
        expr=sum(model.trainees[w] for w in weeks) == target_new
    )

    # Skilled worker balance: for each week, available skilled workers come from
    # initial pool + trained workers (who finished training) - those currently training / training
    # We track trained workers that are "active skilled" after finishing training.
    # Number of trained workers that completed training before week w (available for production):
    model.finished_trained = pyo.Expression(
        weeks,
        rule=lambda m, w: sum(
            m.trainees[t] for t in weeks if t + n_train_weeks <= w
        ),
    )

    # Number of skilled workers in training (either as trainers or being in initial pool):
    # In a training block starting at week t, trainers are out of production for weeks t..t+n-1
    model.skilled_in_training = pyo.Expression(
        weeks,
        rule=lambda m, w: sum(
            m.trainers[t] for t in weeks if t <= w <= t + n_train_weeks - 1
        ),
    )

    # Total skilled workers pool available (initial + finished trained, but trainees becoming skilled)
    # The people in production as skilled are either initial skilled or finished-trained.
    # Constraints on skilled worker allocation each week:
    # number of skilled workers producing (normal + overtime) <= available skilled (initial + finished trained)
    for w in weeks:
        expr_lhs = (
            model.prod_skilled_normal[w]
            + model.prod_skilled_overtime[w]
        )
        # initial skilled reduces by those in training
        avail = init_skilled + model.finished_trained[w]
        model.add_component(
            f"skilled_avail_{w}",
            pyo.Constraint(expr=expr_lhs <= avail),
        )

    # Trained workers (now skilled) production constraints
    for w in weeks:
        model.add_component(
            f"trained_avail_{w}",
            pyo.Constraint(
                expr=model.prod_trained_normal[w] + model.prod_trained_overtime[w]
                <= model.finished_trained[w]
            ),
        )

    # Total skilled-equivalent production capacity (initial skilled workers producing are constrained above;
    # but we also must ensure the training trainers are from initial skilled pool, not from finished trained)
    # Total trainers + producing skilled from initial pool <= initial_skilled
    for w in weeks:
        model.add_component(
            f"init_skilled_total_{w}",
            pyo.Constraint(
                expr=model.prod_skilled_normal[w]
                + model.prod_skilled_overtime[w]
                + model.skilled_in_training[w]
                <= init_skilled
            ),
        )

    # Production capacity from hours: each week, total skilled-equivalent hours
    # Normal-hours contribution
    for w in weeks:
        hours_available = (
            model.prod_skilled_normal[w] * hours_normal
            + model.prod_trained_normal[w] * hours_normal
            + model.prod_skilled_overtime[w] * hours_overtime
            + model.prod_trained_overtime[w] * hours_overtime
        )
        model.add_component(
            f"prod_capacity_{w}",
            pyo.Constraint(
                expr=model.prod_food_I[w] / rate_I + model.prod_food_II[w] / rate_II
                <= hours_available
            ),
        )

    # Demand / shortage balance
    for w in weeks:
        model.add_component(
            f"demand_I_{w}",
            pyo.Constraint(
                expr=model.prod_food_I[w] + model.shortage_I[w] >= dem_I[w - 1]
            ),
        )
        model.add_component(
            f"demand_II_{w}",
            pyo.Constraint(
                expr=model.prod_food_II[w] + model.shortage_II[w] >= dem_II[w - 1]
            ),
        )

    # ---- Objective ----
    def obj_rule(m):
        # Salaries: skilled workers (initial) always paid skilled salary
        # Overtime premium: overtime workers paid sal_overtime instead of sal_skilled
        # Trainees paid training salary during training, then after-training salary once trained
        cost_skilled_base = 0
        cost_overtime_premium = 0
        cost_trainee_training = 0
        cost_trainee_after = 0
        cost_penalty = 0

        for w in weeks:
            # Initial skilled workers all get base salary
            cost_skilled_base += init_skilled * sal_skilled
            # Overtime skilled workers: paid sal_overtime (replaces base for those assigned OT)
            cost_overtime_premium += (
                m.prod_skilled_overtime[w] + m.prod_trained_overtime[w]
            ) * (sal_overtime - sal_skilled)
            # Trainees in training
            cost_trainee_training += m.trainees[w] * sal_trainee_train
            # Finished trainees get after-training salary (skilled-like salary)
            cost_trainee_after += m.finished_trained[w] * sal_trainee_after
            # Shortage penalties
            cost_penalty += (
                m.shortage_I[w] * pen_I + m.shortage_II[w] * pen_II
            )

        # Note: base salary for finished trained workers handled by cost_trainee_after;
        # for those assigned overtime we already added premium relative to sal_skilled
        return (
            cost_skilled_base
            + cost_overtime_premium
            + cost_trainee_training
            + cost_trainee_after
            + cost_penalty
        )

    model.cost = pyo.Expression(rule=obj_rule)
    model.objective = pyo.Objective(expr=model.cost, sense=pyo.minimize)

    # ---- Solve ----
    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}