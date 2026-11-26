# IR: {"sets":{"T":[1,2,3,4,5,6]},"params":["workers_initial","prod_per_worker","demand","overtime_max_per_worker","overtime_unit_cost","holding_cost","max_workforce_change","hiring_cost","layoff_cost","initial_inventory","final_inventory"],"variables":{"workers[t]":"nonnegative integer","hired[t]":"nonnegative integer","laid_off[t]":"nonnegative integer","overtime[t]":"nonnegative continuous","inventory[t]":"nonnegative continuous"},"constraints":["workers[t] = (workers_initial if t=1 else workers[t-1]) + hired[t] - laid_off[t]","hired[t] + laid_off[t] <= max_workforce_change","overtime[t] <= overtime_max_per_worker * workers[t]","inventory[t] = (initial_inventory if t=1 else inventory[t-1]) + prod_per_worker * workers[t] + overtime[t] - demand[t-1]","inventory[6] = final_inventory"],"objective":"minimize sum_t(overtime_unit_cost*overtime[t] + holding_cost*inventory[t] + hiring_cost*hired[t] + layoff_cost*laid_off[t])","continuous_relaxation":"replace all integer domains with nonnegative continuous domains"}
#
# No selling prices or regular wages are supplied. Since demand must be met,
# sales revenue is fixed; minimizing the specified costs maximizes profit
# up to that unknown, constant revenue.
#
# Regular production equals workforce times monthly production per worker.
# Holding cost applies to each month's ending inventory.
#
# solve(params) solves the integer workforce model.
# solve_relaxed(params) solves its continuous relaxation.
# The relaxed minimum cost cannot exceed the integer minimum cost.
# Their objective difference is:
#     solve(params)["objective"] - solve_relaxed(params)["objective"]
# whenever both calls succeed.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _build_model(params, relax_integrality=False):
    workers_initial = params["workers_initial"]
    prod_per_worker = params["prod_per_worker"]
    demand = params["demand"]
    overtime_max_per_worker = params["overtime_max_per_worker"]
    overtime_unit_cost = params["overtime_unit_cost"]
    holding_cost = params["holding_cost"]
    max_workforce_change = params["max_workforce_change"]
    hiring_cost = params["hiring_cost"]
    layoff_cost = params["layoff_cost"]
    initial_inventory = params["initial_inventory"]
    final_inventory = params["final_inventory"]

    if len(demand) != 6:
        raise ValueError("demand must contain exactly six monthly values.")

    model = pyo.ConcreteModel()
    model.months = pyo.RangeSet(1, 6)

    workforce_domain = (
        pyo.NonNegativeReals
        if relax_integrality
        else pyo.NonNegativeIntegers
    )

    model.workers = pyo.Var(model.months, domain=workforce_domain)
    model.hired = pyo.Var(model.months, domain=workforce_domain)
    model.laid_off = pyo.Var(model.months, domain=workforce_domain)
    model.overtime = pyo.Var(model.months, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.months, domain=pyo.NonNegativeReals)

    def workforce_balance_rule(mdl, t):
        previous_workers = (
            workers_initial if t == 1 else mdl.workers[t - 1]
        )
        return (
            mdl.workers[t]
            == previous_workers + mdl.hired[t] - mdl.laid_off[t]
        )

    model.workforce_balance = pyo.Constraint(
        model.months, rule=workforce_balance_rule
    )

    model.workforce_change_limit = pyo.Constraint(
        model.months,
        rule=lambda mdl, t: (
            mdl.hired[t] + mdl.laid_off[t] <= max_workforce_change
        ),
    )

    model.overtime_limit = pyo.Constraint(
        model.months,
        rule=lambda mdl, t: (
            mdl.overtime[t]
            <= overtime_max_per_worker * mdl.workers[t]
        ),
    )

    def inventory_balance_rule(mdl, t):
        previous_inventory = (
            initial_inventory if t == 1 else mdl.inventory[t - 1]
        )
        return (
            mdl.inventory[t]
            == previous_inventory
            + prod_per_worker * mdl.workers[t]
            + mdl.overtime[t]
            - demand[t - 1]
        )

    model.inventory_balance = pyo.Constraint(
        model.months, rule=inventory_balance_rule
    )

    model.final_inventory_requirement = pyo.Constraint(
        expr=model.inventory[6] == final_inventory
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            overtime_unit_cost * model.overtime[t]
            + holding_cost * model.inventory[t]
            + hiring_cost * model.hired[t]
            + layoff_cost * model.laid_off[t]
            for t in model.months
        ),
        sense=pyo.minimize,
    )

    return model


def _solve_model(model):
    # HiGHS may raise RuntimeError when no feasible solution can be loaded.
    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    # Success is determined solely by retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}


def solve(params):
    model = _build_model(params, relax_integrality=False)
    return _solve_model(model)


def solve_relaxed(params):
    model = _build_model(params, relax_integrality=True)
    return _solve_model(model)