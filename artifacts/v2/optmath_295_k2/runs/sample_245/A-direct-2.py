import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    restaurants = [0, 1]
    shifts = [0, 1]
    employees = [0, 1, 2, 3, 4, 5]

    # Demand per (restaurant, shift)
    demand = {
        (0, 0): params["demand_R0_S0"],
        (0, 1): params["demand_R0_S1"],
        (1, 0): params["demand_R1_S0"],
        (1, 1): params["demand_R1_S1"],
    }

    penalty = params["penalty"]

    # Employees with Skill 0
    skilled = {1, 2, 3, 4}

    # Preference cost per employee per shift (only for their available shifts)
    pref_cost = {
        (1, 0): params["pref_cost_E1"],
        (1, 1): params["pref_cost_E1"],
        (2, 0): params["pref_cost_E2"],
        (2, 1): params["pref_cost_E2"],
        (3, 0): params["pref_cost_E3"],
        (4, 0): params["pref_cost_E4"],
        (4, 1): params["pref_cost_E4"],
    }

    # Availability: (employee, shift) pairs where employee is available
    available = {
        (1, 0), (1, 1),
        (2, 0), (2, 1),
        (3, 0),                 # Employee 3 unavailable for Shift 1
        (4, 0), (4, 1),
        (5, 0), (5, 1),
    }

    # Assignment variables: x[employee, restaurant, shift]
    model.x = pyo.Var(employees, restaurants, shifts, domain=pyo.Binary)

    # Unfulfilled variables: u[restaurant, shift] >= 0
    model.u = pyo.Var(restaurants, shifts, domain=pyo.NonNegativeIntegers)

    # Objective
    def obj_rule(m):
        assign_cost = sum(
            pref_cost[(e, s)] * m.x[e, r, s]
            for e in employees
            for r in restaurants
            for s in shifts
            if (e, s) in available and (e, s) in pref_cost
        )
        unfulfilled_cost = sum(
            penalty * m.u[r, s] for r in restaurants for s in shifts
        )
        return assign_cost + unfulfilled_cost

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Demand constraints: sum of assignments + unfulfilled = demand
    def demand_rule(m, r, s):
        return (
            sum(m.x[e, r, s] for e in employees) + m.u[r, s] == demand[(r, s)]
        )

    model.demand_con = pyo.Constraint(restaurants, shifts, rule=demand_rule)

    # Availability constraints: cannot assign to unavailable shift
    def availability_rule(m, e, r, s):
        if (e, s) not in available:
            return m.x[e, r, s] == 0
        return pyo.Constraint.Skip

    model.avail_con = pyo.Constraint(
        employees, restaurants, shifts, rule=availability_rule
    )

    # Skill constraints: unskilled employees cannot be assigned
    def skill_rule(m, e, r, s):
        if e not in skilled:
            return m.x[e, r, s] == 0
        return pyo.Constraint.Skip

    model.skill_con = pyo.Constraint(
        employees, restaurants, shifts, rule=skill_rule
    )

    # Each employee assigned to at most one shift across all restaurants
    def one_shift_rule(m, e):
        return sum(
            m.x[e, r, s] for r in restaurants for s in shifts
        ) <= 1

    model.one_shift_con = pyo.Constraint(employees, rule=one_shift_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}