# IR (JSON):
# {"sets":{"W":"weeks 1..8","F":["I","II"],"S":"training starts 1..(9-D)","A[w]":"s in S with s<=w<s+D","C[w]":"s in S with s+D<=w"},"params":["prod_rate_I","prod_rate_II","initial_skilled_workers","target_new_workers","weekly_hours_normal","weekly_hours_overtime","max_trainees_per_trainer","training_duration_weeks","salary_skilled_weekly","salary_trainee_training_weekly","salary_trainee_after_weekly","salary_overtime_weekly","penalty_shortage_I","penalty_shortage_II","demand_I","demand_II"],"variables":{"trainees[s]":"nonnegative integer","trainers[s]":"nonnegative integer","original_normal[w]":"nonnegative integer","original_overtime[w]":"nonnegative integer","new_normal[w]":"nonnegative integer","new_overtime[w]":"nonnegative integer","hours[w,f]":"nonnegative continuous","shortage[w,f]":"nonnegative continuous"},"constraints":["sum_s trainees[s] = target_new_workers","trainees[s] <= max_trainees_per_trainer * trainers[s]","original_normal[w] + original_overtime[w] + sum_A[w] trainers[s] = initial_skilled_workers","new_normal[w] + new_overtime[w] = sum_C[w] trainees[s]","sum_f hours[w,f] <= weekly_hours_normal*(original_normal[w]+new_normal[w]) + weekly_hours_overtime*(original_overtime[w]+new_overtime[w])","prod_rate[f]*hours[w,f] + shortage[w,f] = demand[w,f]"],"objective":"minimize sum_w {salary_skilled_weekly*(original_normal[w]+sum_A[w] trainers[s]) + salary_trainee_training_weekly*sum_A[w] trainees[s] + salary_trainee_after_weekly*new_normal[w] + salary_overtime_weekly*(original_overtime[w]+new_overtime[w]) + sum_f penalty_shortage[f]*shortage[w,f]}","assumptions":["Demand inputs are already in kg; production rates are kg/hour.","Only original skilled workers train; trainers remain assigned throughout each cohort's training.","Training finishes at the end of start_week+D-1; graduates can produce the following week.","Either class of qualified production worker may work overtime; overtime salary replaces normal salary.","All available qualified workers receive a weekly salary, including workers with unused production hours.","Production hours are divisible between foods; no inventory, backlog, or separate shift-capacity restriction is modeled."]}

from collections.abc import Mapping
import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    rate_I = float(params["prod_rate_I"])
    rate_II = float(params["prod_rate_II"])
    initial_workers_raw = params["initial_skilled_workers"]
    target_workers_raw = params["target_new_workers"]
    normal_hours = float(params["weekly_hours_normal"])
    overtime_hours = float(params["weekly_hours_overtime"])
    training_capacity = float(params["max_trainees_per_trainer"])
    duration_raw = params["training_duration_weeks"]
    skilled_salary = float(params["salary_skilled_weekly"])
    training_salary = float(params["salary_trainee_training_weekly"])
    graduate_salary = float(params["salary_trainee_after_weekly"])
    overtime_salary = float(params["salary_overtime_weekly"])
    penalty_I = float(params["penalty_shortage_I"])
    penalty_II = float(params["penalty_shortage_II"])
    demand_I_input = params["demand_I"]
    demand_II_input = params["demand_II"]

    def integer_parameter(value, label, minimum):
        numeric = float(value)
        if (
            not math.isfinite(numeric)
            or not numeric.is_integer()
            or numeric < minimum
        ):
            raise ValueError(
                f"{label} must be an integer greater than or equal to {minimum}."
            )
        return int(numeric)

    initial_workers = integer_parameter(
        initial_workers_raw, "initial_skilled_workers", 0
    )
    target_workers = integer_parameter(
        target_workers_raw, "target_new_workers", 0
    )
    duration = integer_parameter(
        duration_raw, "training_duration_weeks", 1
    )

    weeks = tuple(range(1, 9))
    foods = ("I", "II")
    starts = tuple(range(1, 10 - duration))

    nonnegative_parameters = {
        "prod_rate_I": rate_I,
        "prod_rate_II": rate_II,
        "weekly_hours_normal": normal_hours,
        "weekly_hours_overtime": overtime_hours,
        "max_trainees_per_trainer": training_capacity,
        "salary_skilled_weekly": skilled_salary,
        "salary_trainee_training_weekly": training_salary,
        "salary_trainee_after_weekly": graduate_salary,
        "salary_overtime_weekly": overtime_salary,
        "penalty_shortage_I": penalty_I,
        "penalty_shortage_II": penalty_II,
    }
    for label, value in nonnegative_parameters.items():
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{label} must be finite and nonnegative.")

    def weekly_demands(values, label):
        # Sequences use positions 0..7. Mappings use week keys 1..8
        # or their string equivalents.
        if isinstance(values, Mapping):
            result = {
                week: float(
                    values[week] if week in values else values[str(week)]
                )
                for week in weeks
            }
        else:
            sequence = list(values)
            if len(sequence) != len(weeks):
                raise ValueError(f"{label} must contain eight weekly demands.")
            result = {
                week: float(sequence[week - 1])
                for week in weeks
            }

        if any(
            not math.isfinite(value) or value < 0
            for value in result.values()
        ):
            raise ValueError(f"{label} must contain finite, nonnegative demands.")
        return result

    demand_I = weekly_demands(demand_I_input, "demand_I")
    demand_II = weekly_demands(demand_II_input, "demand_II")

    rates = {"I": rate_I, "II": rate_II}
    penalties = {"I": penalty_I, "II": penalty_II}
    demands = {
        (week, food): demand_I[week] if food == "I" else demand_II[week]
        for week in weeks
        for food in foods
    }
    active_starts = {
        week: tuple(
            start for start in starts
            if start <= week < start + duration
        )
        for week in weeks
    }
    completed_starts = {
        week: tuple(
            start for start in starts
            if start + duration <= week
        )
        for week in weeks
    }

    model = pyo.ConcreteModel()
    model.W = pyo.Set(initialize=weeks, ordered=True)
    model.F = pyo.Set(initialize=foods, ordered=True)
    model.S = pyo.Set(initialize=starts, ordered=True)

    model.trainees = pyo.Var(model.S, domain=pyo.NonNegativeIntegers)
    model.trainers = pyo.Var(model.S, domain=pyo.NonNegativeIntegers)
    model.original_normal = pyo.Var(model.W, domain=pyo.NonNegativeIntegers)
    model.original_overtime = pyo.Var(model.W, domain=pyo.NonNegativeIntegers)
    model.new_normal = pyo.Var(model.W, domain=pyo.NonNegativeIntegers)
    model.new_overtime = pyo.Var(model.W, domain=pyo.NonNegativeIntegers)
    model.hours = pyo.Var(model.W, model.F, domain=pyo.NonNegativeReals)
    model.shortage = pyo.Var(model.W, model.F, domain=pyo.NonNegativeReals)

    # A symbolic zero also handles an empty feasible training-start set.
    model.training_target = pyo.Constraint(
        expr=(
            pyo.quicksum(model.trainees[start] for start in starts)
            + 0 * model.original_normal[weeks[0]]
            == target_workers
        )
    )

    def training_capacity_rule(block, start):
        return (
            block.trainees[start]
            <= training_capacity * block.trainers[start]
        )

    model.training_capacity_limit = pyo.Constraint(
        model.S, rule=training_capacity_rule
    )

    def original_workforce_rule(block, week):
        return (
            block.original_normal[week]
            + block.original_overtime[week]
            + pyo.quicksum(
                block.trainers[start] for start in active_starts[week]
            )
            == initial_workers
        )

    model.original_workforce_balance = pyo.Constraint(
        model.W, rule=original_workforce_rule
    )

    def graduate_workforce_rule(block, week):
        return (
            block.new_normal[week] + block.new_overtime[week]
            == pyo.quicksum(
                block.trainees[start] for start in completed_starts[week]
            )
        )

    model.graduate_workforce_balance = pyo.Constraint(
        model.W, rule=graduate_workforce_rule
    )

    def production_capacity_rule(block, week):
        return (
            pyo.quicksum(block.hours[week, food] for food in foods)
            <= normal_hours
            * (block.original_normal[week] + block.new_normal[week])
            + overtime_hours
            * (block.original_overtime[week] + block.new_overtime[week])
        )

    model.production_capacity_limit = pyo.Constraint(
        model.W, rule=production_capacity_rule
    )

    def demand_balance_rule(block, week, food):
        return (
            rates[food] * block.hours[week, food]
            + block.shortage[week, food]
            == demands[week, food]
        )

    model.weekly_demand_balance = pyo.Constraint(
        model.W, model.F, rule=demand_balance_rule
    )

    model.total_cost = pyo.Objective(
        expr=pyo.quicksum(
            skilled_salary
            * (
                model.original_normal[week]
                + pyo.quicksum(
                    model.trainers[start]
                    for start in active_starts[week]
                )
            )
            + training_salary
            * pyo.quicksum(
                model.trainees[start]
                for start in active_starts[week]
            )
            + graduate_salary * model.new_normal[week]
            + overtime_salary
            * (model.original_overtime[week] + model.new_overtime[week])
            + pyo.quicksum(
                penalties[food] * model.shortage[week, food]
                for food in foods
            )
            for week in weeks
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when its automatic solution loading finds
        # no feasible solution. Unexpected runtime errors propagate.
        message = str(exc).lower()
        if (
            "feasible solution was not found" in message
            and "no solution can be loaded" in message
        ):
            return {"objective": None, "status": "no_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}