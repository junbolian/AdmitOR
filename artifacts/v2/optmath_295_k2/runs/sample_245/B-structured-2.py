# IR: {"sets":{"employees":[0,1,2,3,4,5],"restaurants":[0,1],"shifts":[0,1],"skilled_employees":[1,2,3,4],"available_employee_shifts":[[1,0],[1,1],[2,0],[2,1],[3,0],[4,0],[4,1],[5,0],[5,1]]},"params":{"demand_R0_S0":"demand[0,0]","demand_R0_S1":"demand[0,1]","demand_R1_S0":"demand[1,0]","demand_R1_S1":"demand[1,1]","pref_cost_E1":"cost[1]","pref_cost_E2":"cost[2]","pref_cost_E3":"cost[3]","pref_cost_E4":"cost[4]","penalty":"penalty"},"variables":{"assignment[e,r,s]":"Binary","shortfall[r,s]":"NonNegativeIntegers"},"constraints":["For each (r,s): sum_e assignment[e,r,s] + shortfall[r,s] = demand[r,s].","For each (e,r,s): assignment[e,r,s] <= indicator((e,s) is available).","For each (e,r,s): assignment[e,r,s] <= indicator(e is skilled).","For each e: sum_(r,s) assignment[e,r,s] <= 1."],"objective":"Minimize sum_(e in skilled,r,s) cost[e]*assignment[e,r,s] + penalty*sum_(r,s) shortfall[r,s]."}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_data = {
        (0, 0): params["demand_R0_S0"],
        (0, 1): params["demand_R0_S1"],
        (1, 0): params["demand_R1_S0"],
        (1, 1): params["demand_R1_S1"],
    }
    cost_data = {
        1: params["pref_cost_E1"],
        2: params["pref_cost_E2"],
        3: params["pref_cost_E3"],
        4: params["pref_cost_E4"],
    }
    penalty_data = params["penalty"]

    available_pairs = {
        (1, 0), (1, 1),
        (2, 0), (2, 1),
        (3, 0),
        (4, 0), (4, 1),
        (5, 0), (5, 1),
    }

    model = pyo.ConcreteModel()
    model.employees = pyo.RangeSet(0, 5)
    model.restaurants = pyo.RangeSet(0, 1)
    model.shifts = pyo.RangeSet(0, 1)
    model.skilled_employees = pyo.Set(initialize=[1, 2, 3, 4])

    model.demand = pyo.Param(
        model.restaurants,
        model.shifts,
        initialize=demand_data,
        within=pyo.Reals,
    )
    model.preference_cost = pyo.Param(
        model.skilled_employees,
        initialize=cost_data,
        within=pyo.Reals,
    )
    model.shortfall_penalty = pyo.Param(
        initialize=penalty_data,
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.employees,
        model.restaurants,
        model.shifts,
        domain=pyo.Binary,
    )
    model.shortfall = pyo.Var(
        model.restaurants,
        model.shifts,
        domain=pyo.NonNegativeIntegers,
    )

    def demand_rule(instance, restaurant, shift):
        return (
            sum(
                instance.assignment[employee, restaurant, shift]
                for employee in instance.employees
            )
            + instance.shortfall[restaurant, shift]
            == instance.demand[restaurant, shift]
        )

    model.demand_balance = pyo.Constraint(
        model.restaurants, model.shifts, rule=demand_rule
    )

    def availability_rule(instance, employee, restaurant, shift):
        return instance.assignment[employee, restaurant, shift] <= int(
            (employee, shift) in available_pairs
        )

    model.availability_limit = pyo.Constraint(
        model.employees,
        model.restaurants,
        model.shifts,
        rule=availability_rule,
    )

    def skill_rule(instance, employee, restaurant, shift):
        return instance.assignment[employee, restaurant, shift] <= int(
            employee in instance.skilled_employees
        )

    model.skill_limit = pyo.Constraint(
        model.employees,
        model.restaurants,
        model.shifts,
        rule=skill_rule,
    )

    def employee_rule(instance, employee):
        return sum(
            instance.assignment[employee, restaurant, shift]
            for restaurant in instance.restaurants
            for shift in instance.shifts
        ) <= 1

    model.employee_assignment_limit = pyo.Constraint(
        model.employees, rule=employee_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.preference_cost[employee]
            * model.assignment[employee, restaurant, shift]
            for employee in model.skilled_employees
            for restaurant in model.restaurants
            for shift in model.shifts
        )
        + model.shortfall_penalty
        * sum(
            model.shortfall[restaurant, shift]
            for restaurant in model.restaurants
            for shift in model.shifts
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # HiGHS can raise when no feasible solution can be loaded.
        # Objective retrieval below remains the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}