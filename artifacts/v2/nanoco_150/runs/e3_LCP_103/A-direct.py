import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    conflict_pairs = params["conflict_pairs"]

    exams = list(range(8))
    allowable = {
        i: list(params[f"allowable_slots_exam{i}"])
        for i in exams
    }

    # All distinct slots appearing anywhere
    all_slots = sorted({s for i in exams for s in allowable[i]})

    # Mapping exam -> positions in its allowable list
    def slot_positions(i):
        return list(range(len(allowable[i])))

    model = pyo.ConcreteModel()

    model.EXAMS = pyo.Set(initialize=exams)

    model.x = pyo.Var(model.EXAMS, domain=pyo.Integers, bounds=lambda m, i: (0, len(allowable[i]) - 1))

    model.z = pyo.Var(domain=pyo.Reals)

    # Each exam maps to a slot in its allowable list
    model.slot_index = pyo.Expression(
        model.EXAMS,
        rule=lambda m, i: allowable[i][0]
        if len(allowable[i]) == 1
        else sum(allowable[i][k] * m.x[i] ** 0 for k in [0])  # placeholder overwritten below
    )
    model.del_component('slot_index')

    # Slot of exam = allowable[i][position]
    def slot_of(m, i):
        return pyo.quicksum(allowable[i][k] * m.x[i] for k in [0]) if False else None

    # Build explicit linear expression: slot value as weighted selection is nonlinear,
    # so use a binary assignment formulation for correctness and linearity.

    model.del_component('x')

    model.y = pyo.Var(
        [(i, s) for i in exams for s in allowable[i]],
        domain=pyo.Binary
    )

    # Each exam assigned exactly one allowable slot
    model.assign = pyo.Constraint(
        model.EXAMS,
        rule=lambda m, i: pyo.quicksum(m.y[i, s] for s in allowable[i]) == 1
    )

    # Exam slot value
    model.slot_val = pyo.Expression(
        model.EXAMS,
        rule=lambda m, i: pyo.quicksum(s * m.y[i, s] for s in allowable[i])
    )

    # z >= slot value of every exam
    model.max_con = pyo.Constraint(
        model.EXAMS,
        rule=lambda m, i: m.z >= m.slot_val[i]
    )

    # Conflict constraints
    model.conflicts = pyo.ConstraintList()
    for (a, b) in conflict_pairs:
        for s in set(allowable[a]) & set(allowable[b]):
            model.conflicts.add(model.y[a, s] + model.y[b, s] <= 1)

    model.obj = pyo.Objective(expr=model.z, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}