import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural constants
    batches = [0, 1, 2]
    stages = [0, 1, 2]

    # Routes: batch -> list of units per stage (SOP order)
    route_units = {
        0: [1, 2, 0],
        1: [1, 0, 2],
        2: [2, 1, 0],
    }

    # Processing time reader — keyed by the actual unit used in that stage
    def ptime(batch, stage):
        unit = route_units[batch][stage]
        key = "processing_time_B%d_on_U%d_stage%d" % (batch, unit, stage + 1)
        return params[key]

    model = pyo.ConcreteModel()

    model.OPS = pyo.Set(initialize=[(b, s) for b in batches for s in stages])

    model.start = pyo.Var(model.OPS, within=pyo.NonNegativeReals)
    model.makespan = pyo.Var(within=pyo.NonNegativeReals)

    def completion_rule(m, b, s):
        return m.start[b, s] + ptime(b, s)

    model.completion = pyo.Expression(model.OPS, rule=completion_rule)

    def precedence_rule(m, b, s):
        if s == 0:
            return pyo.Constraint.Skip
        return m.start[b, s] >= m.completion[b, s - 1]

    model.precedence = pyo.Constraint(model.OPS, rule=precedence_rule)

    def makespan_rule(m, b, s):
        return m.makespan >= m.completion[b, s]

    model.makespan_con = pyo.Constraint(model.OPS, rule=makespan_rule)

    # Pairs of operations sharing a unit
    pair_list = []
    for unit in [0, 1, 2]:
        ops_on_unit = []
        for b in batches:
            for s in stages:
                if route_units[b][s] == unit:
                    ops_on_unit.append((b, s))
        for i in range(len(ops_on_unit)):
            for j in range(i + 1, len(ops_on_unit)):
                pair_list.append((ops_on_unit[i], ops_on_unit[j]))

    model.PAIRS = pyo.Set(initialize=pair_list, dimen=2)
    model.y = pyo.Var(model.PAIRS, within=pyo.Binary)

    total_time = sum(ptime(b, s) for b in batches for s in stages)

    def disjunctive_rule(m, p):
        op_i, op_j = p
        return (m.start[op_i] + ptime(op_i[0], op_i[1])
                <= m.start[op_j] + total_time * (1 - m.y[p]),
                m.start[op_j] + ptime(op_j[0], op_j[1])
                <= m.start[op_i] + total_time * m.y[p])

    model.disjunctive = pyo.Constraint(model.PAIRS, rule=disjunctive_rule)

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}