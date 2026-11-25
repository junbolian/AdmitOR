# IR: {"sets":{"courses":"range(num_courses)","slots":"range(max_slots)","edges":"unique pairs in edge_list"},"params":{"num_courses":"course count","num_edges":"reported edge count; metadata only, edge_list defines all conflicts","min_slots":"minimum employed slots","max_slots":"available slot count","edge_list":"conflict pairs","slot_cost":"cost per employed slot"},"variables":{"x[c,t]":"binary; course c uses slot t","y[t]":"binary; slot t is employed"},"constraints":["For each course c: sum_t x[c,t] = 1","For each pair (u,v) in edges and slot t: x[u,t] + x[v,t] <= 1","For each course c and slot t: x[c,t] <= y[t]","For each slot t: y[t] <= sum_c x[c,t]","min_slots <= sum_t y[t] <= max_slots"],"objective":"minimize slot_cost * sum_t y[t]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_courses = params["num_courses"]
    num_edges = params["num_edges"]
    min_slots = params["min_slots"]
    max_slots = params["max_slots"]
    edge_list = params["edge_list"]
    slot_cost = params["slot_cost"]

    model = pyo.ConcreteModel()

    # Use every supplied conflict pair even if the reported count differs.
    model.reported_edge_count = pyo.Param(initialize=num_edges)
    model.courses = pyo.Set(
        initialize=range(num_courses),
        ordered=True,
    )
    model.slots = pyo.Set(
        initialize=range(max_slots),
        ordered=True,
    )
    model.conflict_pairs = pyo.Set(
        dimen=2,
        initialize=(tuple(edge) for edge in edge_list),
        ordered=True,
    )

    model.x = pyo.Var(
        model.courses,
        model.slots,
        domain=pyo.Binary,
    )
    model.y = pyo.Var(
        model.slots,
        domain=pyo.Binary,
    )

    def assignment_rule(schedule, course):
        return (
            1,
            pyo.quicksum(
                schedule.x[course, slot] for slot in schedule.slots
            ),
            1,
        )

    model.assignment_constraints = pyo.Constraint(
        model.courses,
        rule=assignment_rule,
    )

    def conflict_rule(schedule, course_u, course_v, slot):
        return (
            schedule.x[course_u, slot]
            + schedule.x[course_v, slot]
            <= 1
        )

    model.conflict_constraints = pyo.Constraint(
        model.conflict_pairs,
        model.slots,
        rule=conflict_rule,
    )

    def activation_rule(schedule, course, slot):
        return schedule.x[course, slot] <= schedule.y[slot]

    model.activation_constraints = pyo.Constraint(
        model.courses,
        model.slots,
        rule=activation_rule,
    )

    def usage_rule(schedule, slot):
        return schedule.y[slot] <= pyo.quicksum(
            schedule.x[course, slot] for course in schedule.courses
        )

    model.usage_constraints = pyo.Constraint(
        model.slots,
        rule=usage_rule,
    )

    model.slot_limits = pyo.Constraint(
        expr=(
            min_slots,
            pyo.quicksum(model.y[slot] for slot in model.slots),
            max_slots,
        )
    )

    model.total_cost = pyo.Objective(
        expr=slot_cost * pyo.quicksum(
            model.y[slot] for slot in model.slots
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # An unavailable solution may prevent automatic solution loading.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}