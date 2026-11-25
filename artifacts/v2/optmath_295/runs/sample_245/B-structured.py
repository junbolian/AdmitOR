# IR: {"sets":{"E":[0,1,2,3,4,5],"R":[0,1],"S":[0,1],"Q":[1,2,3,4],"A":[[1,0],[1,1],[2,0],[2,1],[3,0],[4,0],[4,1],[5,0],[5,1]]},"params":{"demand[r,s]":["demand_R0_S0","demand_R0_S1","demand_R1_S0","demand_R1_S1"],"cost[e]":["pref_cost_emp1","pref_cost_emp2","pref_cost_emp3","pref_cost_emp4"],"penalty":"penalty_per_unfulfilled"},"variables":{"x[e,r,s]":"Binary","unfilled[r,s]":"NonNegativeInteger"},"constraints":["sum(e in E,x[e,r,s])+unfilled[r,s]=demand[r,s] for all r,s","x[e,r,s]<=1 if (e,s) in A else x[e,r,s]<=0 for all e,r,s","x[e,r,s]<=1 if e in Q else x[e,r,s]<=0 for all e,r,s","sum(r in R,s in S,x[e,r,s])<=1 for all e"],"objective":"min sum(e in Q,r in R,s in S,cost[e]*x[e,r,s])+penalty*sum(r in R,s in S,unfilled[r,s])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.employees = pyo.Set(initialize=range(6), ordered=True)
    model.restaurants = pyo.Set(initialize=range(2), ordered=True)
    model.shifts = pyo.Set(initialize=range(2), ordered=True)
    model.skilled_employees = pyo.Set(
        within=model.employees,
        initialize=[1, 2, 3, 4],
        ordered=True,
    )
    model.available_pairs = pyo.Set(
        dimen=2,
        within=model.employees * model.shifts,
        initialize=[
            (1, 0), (1, 1),
            (2, 0), (2, 1),
            (3, 0),
            (4, 0), (4, 1),
            (5, 0), (5, 1),
        ],
    )

    model.staffing_demand = pyo.Param(
        model.restaurants,
        model.shifts,
        initialize={
            (0, 0): params["demand_R0_S0"],
            (0, 1): params["demand_R0_S1"],
            (1, 0): params["demand_R1_S0"],
            (1, 1): params["demand_R1_S1"],
        },
        within=pyo.NonNegativeReals,
    )
    model.preference_cost = pyo.Param(
        model.skilled_employees,
        initialize={
            1: params["pref_cost_emp1"],
            2: params["pref_cost_emp2"],
            3: params["pref_cost_emp3"],
            4: params["pref_cost_emp4"],
        },
        within=pyo.Reals,
    )
    model.shortfall_penalty = pyo.Param(
        initialize=params["penalty_per_unfulfilled"],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.employees,
        model.restaurants,
        model.shifts,
        domain=pyo.Binary,
    )
    model.unfilled = pyo.Var(
        model.restaurants,
        model.shifts,
        domain=pyo.NonNegativeIntegers,
    )

    def demand_rule(mdl, restaurant, shift):
        return (
            sum(
                mdl.assignment[employee, restaurant, shift]
                for employee in mdl.employees
            )
            + mdl.unfilled[restaurant, shift]
            == mdl.staffing_demand[restaurant, shift]
        )

    model.demand_balance = pyo.Constraint(
        model.restaurants, model.shifts, rule=demand_rule
    )

    def availability_rule(mdl, employee, restaurant, shift):
        return mdl.assignment[employee, restaurant, shift] <= (
            1 if (employee, shift) in mdl.available_pairs else 0
        )

    model.availability_limit = pyo.Constraint(
        model.employees,
        model.restaurants,
        model.shifts,
        rule=availability_rule,
    )

    def skill_rule(mdl, employee, restaurant, shift):
        return mdl.assignment[employee, restaurant, shift] <= (
            1 if employee in mdl.skilled_employees else 0
        )

    model.skill_limit = pyo.Constraint(
        model.employees,
        model.restaurants,
        model.shifts,
        rule=skill_rule,
    )

    def employee_limit_rule(mdl, employee):
        return sum(
            mdl.assignment[employee, restaurant, shift]
            for restaurant in mdl.restaurants
            for shift in mdl.shifts
        ) <= 1

    model.employee_limit = pyo.Constraint(
        model.employees, rule=employee_limit_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.preference_cost[employee]
            * model.assignment[employee, restaurant, shift]
            for employee in model.skilled_employees
            for restaurant in model.restaurants
            for shift in model.shifts
        )
        + model.shortfall_penalty * sum(
            model.unfilled[restaurant, shift]
            for restaurant in model.restaurants
            for shift in model.shifts
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" not in str(exc):
            raise
        return {"objective": None, "status": "no_feasible_solution"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}