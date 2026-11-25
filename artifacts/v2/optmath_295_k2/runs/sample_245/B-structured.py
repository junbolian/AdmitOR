# IR: {"sets":{"E":[0,1,2,3,4,5],"R":[0,1],"S":[0,1],"K":[1,2,3,4],"V":[[1,0],[1,1],[2,0],[2,1],[3,0],[4,0],[4,1],[5,0],[5,1]],"A":"{(e,r,s): e in K, r in R, s in S, (e,s) in V}"},"params":{"demand_R0_S0":"d[0,0]","demand_R0_S1":"d[0,1]","demand_R1_S0":"d[1,0]","demand_R1_S1":"d[1,1]","pref_cost_E1":"c[1]","pref_cost_E2":"c[2]","pref_cost_E3":"c[3], used only at Shift 0","pref_cost_E4":"c[4]","penalty":"p"},"variables":{"x[e,r,s]":"Binary, E x R x S","u[r,s]":"NonNegativeIntegers, R x S"},"constraints":["sum(e in E, x[e,r,s]) + u[r,s] = d[r,s] for each (r,s)","x[e,r,s] <= indicator((e,s) in V) for each (e,r,s)","x[e,r,s] <= indicator(e in K) for each (e,r,s)","sum(r in R,s in S,x[e,r,s]) <= 1 for each e"],"objective":"minimize sum((e,r,s) in A,c[e]*x[e,r,s]) + p*sum(r in R,s in S,u[r,s])"}

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
    )

    available_pairs = {
        (1, 0), (1, 1),
        (2, 0), (2, 1),
        (3, 0),
        (4, 0), (4, 1),
        (5, 0), (5, 1),
    }
    model.available_pairs = pyo.Set(
        dimen=2,
        within=model.employees * model.shifts,
        initialize=sorted(available_pairs),
    )
    model.eligible_assignments = pyo.Set(
        dimen=3,
        within=model.employees * model.restaurants * model.shifts,
        initialize=[
            (employee, restaurant, shift)
            for employee in [1, 2, 3, 4]
            for restaurant in range(2)
            for shift in range(2)
            if (employee, shift) in available_pairs
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
    )
    model.preference_cost = pyo.Param(
        model.skilled_employees,
        initialize={
            1: params["pref_cost_E1"],
            2: params["pref_cost_E2"],
            3: params["pref_cost_E3"],
            4: params["pref_cost_E4"],
        },
    )
    model.shortage_penalty = pyo.Param(initialize=params["penalty"])

    model.assignment = pyo.Var(
        model.employees,
        model.restaurants,
        model.shifts,
        domain=pyo.Binary,
    )
    model.unfulfilled = pyo.Var(
        model.restaurants,
        model.shifts,
        domain=pyo.NonNegativeIntegers,
    )

    def demand_rule(model, restaurant, shift):
        return (
            sum(
                model.assignment[employee, restaurant, shift]
                for employee in model.employees
            )
            + model.unfulfilled[restaurant, shift]
            == model.staffing_demand[restaurant, shift]
        )

    model.demand_balance = pyo.Constraint(
        model.restaurants, model.shifts, rule=demand_rule
    )

    def availability_rule(model, employee, restaurant, shift):
        return model.assignment[employee, restaurant, shift] <= int(
            (employee, shift) in model.available_pairs
        )

    model.availability_limit = pyo.Constraint(
        model.employees,
        model.restaurants,
        model.shifts,
        rule=availability_rule,
    )

    def skill_rule(model, employee, restaurant, shift):
        return model.assignment[employee, restaurant, shift] <= int(
            employee in model.skilled_employees
        )

    model.skill_limit = pyo.Constraint(
        model.employees,
        model.restaurants,
        model.shifts,
        rule=skill_rule,
    )

    def employee_rule(model, employee):
        return sum(
            model.assignment[employee, restaurant, shift]
            for restaurant in model.restaurants
            for shift in model.shifts
        ) <= 1

    model.employee_assignment_limit = pyo.Constraint(
        model.employees, rule=employee_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.preference_cost[employee]
            * model.assignment[employee, restaurant, shift]
            for employee, restaurant, shift in model.eligible_assignments
        )
        + model.shortage_penalty
        * sum(
            model.unfulfilled[restaurant, shift]
            for restaurant in model.restaurants
            for shift in model.shifts
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPSI raises this when it cannot load a feasible solution.
        # Still determine success solely by retrieving the objective below.
        if "A feasible solution was not found" not in str(exc):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}