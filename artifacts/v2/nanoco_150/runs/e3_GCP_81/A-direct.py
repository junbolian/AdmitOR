import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_courses = params["num_courses"]
    max_slots = params["max_slots"]
    edge_list = params["edge_list"]
    slot_cost = params["slot_cost"]

    courses = list(range(num_courses))
    slots = list(range(max_slots))

    model = pyo.ConcreteModel()

    model.course_set = pyo.Set(initialize=courses)
    model.slot_set = pyo.Set(initialize=slots)

    model.edges = pyo.Set(initialize=[tuple(e) for e in edge_list], dimen=2)

    model.assign = pyo.Var(model.course_set, model.slot_set, domain=pyo.Binary)
    model.use_slot = pyo.Var(model.slot_set, domain=pyo.Binary)

    def one_slot_rule(m, c):
        return sum(m.assign[c, s] for s in m.slot_set) == 1

    model.one_slot = pyo.Constraint(model.course_set, rule=one_slot_rule)

    def conflict_rule(m, c1, c2, s):
        return m.assign[c1, s] + m.assign[c2, s] <= 1

    model.conflict = pyo.Constraint(
        model.edges, model.slot_set, rule=conflict_rule
    )

    def link_rule(m, c, s):
        return m.assign[c, s] <= m.use_slot[s]

    model.link = pyo.Constraint(model.course_set, model.slot_set, rule=link_rule)

    def obj_rule(m):
        return slot_cost * sum(m.use_slot[s] for s in m.slot_set)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}