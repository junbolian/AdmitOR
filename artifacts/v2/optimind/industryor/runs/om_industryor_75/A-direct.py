import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    parts = list(range(10))          # indices 0..9 represent parts 1..10
    machines = ['A', 'B', 'C']

    processing_cost = {
        'A': params["processing_cost_A"],
        'B': params["processing_cost_B"],
        'C': params["processing_cost_C"],
    }
    setup_cost = {
        'A': params["setup_cost_A"],
        'B': params["setup_cost_B"],
        'C': params["setup_cost_C"],
    }

    model = pyo.ConcreteModel()

    # x[i, m] = 1 if part i+1 processed on machine m
    model.x = pyo.Var(parts, machines, domain=pyo.Binary)

    # y[m] = 1 if machine m is used (setup incurred)
    model.y = pyo.Var(machines, domain=pyo.Binary)

    # Each part on exactly one machine
    model.assign = pyo.Constraint(
        parts,
        rule=lambda model, i: sum(model.x[i, mm] for mm in machines) == 1,
    )

    # Link usage indicator: y[m] >= x[i, m]
    model.link = pyo.Constraint(
        parts, machines,
        rule=lambda model, i, mm: model.y[mm] >= model.x[i, mm],
    )

    # Requirement 2: part 1 and part 2 must be on different machine groups:
    # part1 on A  <=> part2 not on A;  part1 not on A <=> part2 on A
    model.req2a = pyo.Constraint(
        expr=model.x[0, 'A'] == 1 - model.x[1, 'A']
    )
    model.req2b = pyo.Constraint(
        expr=(model.x[0, 'B'] + model.x[0, 'C']) == model.x[1, 'A']
    )

    # Requirement 3: parts 3, 4, 5 fixed to A, B, C respectively
    model.req3a = pyo.Constraint(expr=model.x[2, 'A'] == 1)
    model.req3b = pyo.Constraint(expr=model.x[3, 'B'] == 1)
    model.req3c = pyo.Constraint(expr=model.x[4, 'C'] == 1)

    # Requirement 4: at most max_parts_on_C part types on machine C
    model.req4 = pyo.Constraint(
        expr=sum(model.x[i, 'C'] for i in parts) <= params["max_parts_on_C"]
    )

    # Objective: processing costs + setup costs
    def obj_rule(model):
        proc = sum(
            processing_cost[mm][i] * model.x[i, mm]
            for i in parts for mm in machines
        )
        setup = sum(setup_cost[mm] * model.y[mm] for mm in machines)
        return proc + setup

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {'objective': obj_val, 'status': 'optimal'}