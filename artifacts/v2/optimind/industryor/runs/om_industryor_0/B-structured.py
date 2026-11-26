# IR: {"sets":{"T":"1..8","P":["I","II"],"S":"s in T with s+L-1<=8","A[t]":"s in S with s<=t<s+L","C[t]":"s in S with s+L<=t"},"params":["skilled_workers","new_workers","prod_rate_I","prod_rate_II","weekly_hours_normal","weekly_hours_overtime","train_capacity","train_weeks","wage_skilled","wage_trainee","wage_trained","wage_overtime","penalty_I","penalty_II","demand_I","demand_II"],"assumptions":["Demand arrays have eight entries in chronological order.","weekly_hours_overtime is the total weekly hours of an overtime worker.","Overtime is available to original skilled workers who are not training others.","Training starts at the beginning of a week; graduates produce beginning the week after L full training weeks.","New workers are paid from the start of training.","Production may be stored without holding cost; all demand must be delivered by the end of week 8."],"variables":{"trainees[s]":"nonnegative integer","trainers[s]":"nonnegative integer","overtime[t]":"nonnegative integer","hours[p,t]":"nonnegative continuous","inventory[p,t]":"nonnegative continuous","backlog[p,t]":"nonnegative continuous"},"expressions":{"L":"train_weeks","active_trainers[t]":"sum(trainers[s] for s in A[t])","active_trainees[t]":"sum(trainees[s] for s in A[t])","graduates[t]":"sum(trainees[s] for s in C[t])"},"constraints":["sum(trainees[s] for s in S)=new_workers","trainees[s]<=train_capacity*trainers[s] for s in S","active_trainers[t]<=skilled_workers for t in T","overtime[t]<=skilled_workers-active_trainers[t] for t in T","sum(hours[p,t] for p in P)<=weekly_hours_normal*(skilled_workers-active_trainers[t]+graduates[t])+(weekly_hours_overtime-weekly_hours_normal)*overtime[t] for t in T","inventory[p,t]-backlog[p,t]=inventory[p,t-1]-backlog[p,t-1]+prod_rate[p]*hours[p,t]-demand[p,t] for p in P,t in T, with initial inventory and backlog zero","backlog[p,8]=0 for p in P"],"objective":"minimize sum(wage_skilled*skilled_workers+wage_trainee*active_trainees[t]+wage_trained*graduates[t]+(wage_overtime-wage_skilled)*overtime[t]+sum(penalty[p]*backlog[p,t] for p in P) for t in T)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    skilled_workers = params["skilled_workers"]
    new_workers = params["new_workers"]
    prod_rate_I = params["prod_rate_I"]
    prod_rate_II = params["prod_rate_II"]
    weekly_hours_normal = params["weekly_hours_normal"]
    weekly_hours_overtime = params["weekly_hours_overtime"]
    train_capacity = params["train_capacity"]
    train_weeks = params["train_weeks"]
    wage_skilled = params["wage_skilled"]
    wage_trainee = params["wage_trainee"]
    wage_trained = params["wage_trained"]
    wage_overtime = params["wage_overtime"]
    penalty_I = params["penalty_I"]
    penalty_II = params["penalty_II"]
    demand_I = params["demand_I"]
    demand_II = params["demand_II"]

    training_duration = int(train_weeks)
    if training_duration < 1 or training_duration != train_weeks:
        raise ValueError("train_weeks must be a positive integer.")

    demand_I = list(demand_I)
    demand_II = list(demand_II)
    if len(demand_I) != 8 or len(demand_II) != 8:
        raise ValueError("Each demand sequence must contain eight entries.")

    production_rate = {"I": prod_rate_I, "II": prod_rate_II}
    penalty = {"I": penalty_I, "II": penalty_II}
    demand = {
        (product, week): sequence[week - 1]
        for product, sequence in (("I", demand_I), ("II", demand_II))
        for week in range(1, 9)
    }

    start_weeks = tuple(range(1, 10 - training_duration))
    active_starts = {
        week: tuple(
            start
            for start in start_weeks
            if start <= week < start + training_duration
        )
        for week in range(1, 9)
    }
    completed_starts = {
        week: tuple(
            start
            for start in start_weeks
            if start + training_duration <= week
        )
        for week in range(1, 9)
    }

    model = pyo.ConcreteModel()
    model.weeks = pyo.RangeSet(1, 8)
    model.products = pyo.Set(initialize=("I", "II"), ordered=True)
    model.training_starts = pyo.Set(initialize=start_weeks, ordered=True)

    model.trainees = pyo.Var(
        model.training_starts, domain=pyo.NonNegativeIntegers
    )
    model.trainers = pyo.Var(
        model.training_starts, domain=pyo.NonNegativeIntegers
    )
    model.overtime = pyo.Var(model.weeks, domain=pyo.NonNegativeIntegers)
    model.hours = pyo.Var(
        model.products, model.weeks, domain=pyo.NonNegativeReals
    )
    model.inventory = pyo.Var(
        model.products, model.weeks, domain=pyo.NonNegativeReals
    )
    model.backlog = pyo.Var(
        model.products, model.weeks, domain=pyo.NonNegativeReals
    )

    def active_trainers_rule(instance, week):
        return sum(
            instance.trainers[start] for start in active_starts[week]
        )

    def active_trainees_rule(instance, week):
        return sum(
            instance.trainees[start] for start in active_starts[week]
        )

    def graduates_rule(instance, week):
        return sum(
            instance.trainees[start] for start in completed_starts[week]
        )

    model.active_trainers = pyo.Expression(
        model.weeks, rule=active_trainers_rule
    )
    model.active_trainees = pyo.Expression(
        model.weeks, rule=active_trainees_rule
    )
    model.graduates = pyo.Expression(model.weeks, rule=graduates_rule)

    # A tuple also handles an empty set of feasible training start weeks.
    model.training_target = pyo.Constraint(
        expr=(
            new_workers,
            pyo.quicksum(
                model.trainees[start] for start in model.training_starts
            ),
            new_workers,
        )
    )

    def training_capacity_rule(instance, start):
        return (
            instance.trainees[start]
            <= train_capacity * instance.trainers[start]
        )

    model.training_capacity_limit = pyo.Constraint(
        model.training_starts, rule=training_capacity_rule
    )

    def trainer_availability_rule(instance, week):
        return instance.active_trainers[week] <= skilled_workers

    model.trainer_availability = pyo.Constraint(
        model.weeks, rule=trainer_availability_rule
    )

    def overtime_availability_rule(instance, week):
        return (
            instance.overtime[week]
            <= skilled_workers - instance.active_trainers[week]
        )

    model.overtime_availability = pyo.Constraint(
        model.weeks, rule=overtime_availability_rule
    )

    def production_capacity_rule(instance, week):
        available_hours = weekly_hours_normal * (
            skilled_workers
            - instance.active_trainers[week]
            + instance.graduates[week]
        ) + (
            weekly_hours_overtime - weekly_hours_normal
        ) * instance.overtime[week]
        return (
            sum(
                instance.hours[product, week]
                for product in instance.products
            )
            <= available_hours
        )

    model.production_capacity = pyo.Constraint(
        model.weeks, rule=production_capacity_rule
    )

    def material_balance_rule(instance, product, week):
        previous_net_inventory = (
            0
            if week == 1
            else (
                instance.inventory[product, week - 1]
                - instance.backlog[product, week - 1]
            )
        )
        return (
            instance.inventory[product, week]
            - instance.backlog[product, week]
            == previous_net_inventory
            + production_rate[product] * instance.hours[product, week]
            - demand[product, week]
        )

    model.material_balance = pyo.Constraint(
        model.products, model.weeks, rule=material_balance_rule
    )

    def final_delivery_rule(instance, product):
        return instance.backlog[product, 8] == 0

    model.final_delivery = pyo.Constraint(
        model.products, rule=final_delivery_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            wage_skilled * skilled_workers
            + wage_trainee * model.active_trainees[week]
            + wage_trained * model.graduates[week]
            + (wage_overtime - wage_skilled) * model.overtime[week]
            + sum(
                penalty[product] * model.backlog[product, week]
                for product in model.products
            )
            for week in model.weeks
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}