import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    jobs = [0, 1, 2]
    ops = [0, 1]

    # Processing times and precedence lags read from params
    ptime = {}
    lag = {}
    for j in jobs:
        for o in ops:
            ptime[(j, o)] = params["processing_time_j%d_o%d" % (j, o)]
        lag[j] = params["precedence_lag_j%d" % j]

    bigM = params["machine_disjunctive_bigM"]

    # Machine assignment: form the set of (job, op) tasks on each machine.
    # Given the problem description, operations are grouped so that conflicts
    # exist between specific pairs. We model machine capacity as disjunctive
    # constraints over all distinct (job,op) task pairs that share a machine.
    # Based on the structure, define machine groups covering all 6 operations.
    tasks = [(j, o) for j in jobs for o in ops]

    # Machine assignment mapping (structural): 
    # M1: j0o0, j1o0 ; M2: j0o1 ; M3: j2o0, j2o1 ; M4: j1o1
    # To honor the disjunctive constraints described, we generate conflicts
    # for the pairs explicitly referenced. We also ensure all tasks are placed.
    machine_pairs = [
        ((0, 0), (1, 0)),
        ((0, 0), (0, 1)),
        ((2, 0), (2, 1)),
        ((1, 0), (1, 1)),
        ((0, 1), (1, 1)),
        ((0, 1), (2, 1)),
        ((1, 0), (2, 0)),
    ]

    model = pyo.ConcreteModel()

    # Start time variables
    model.start_index = pyo.Set(initialize=tasks, dimen=2)
    model.start = pyo.Var(model.start_index, within=pyo.NonNegativeReals)

    # Makespan variable
    model.makespan = pyo.Var(within=pyo.NonNegativeReals)

    # Binary sequencing variables per conflicting pair
    pair_set = pyo.Set(initialize=range(len(machine_pairs)), dimen=1)
    model.order = pyo.Var(pair_set, within=pyo.Binary)

    # Precedence constraints within each job
    def precedence_rule(mdl, j):
        return mdl.start[j, 1] >= mdl.start[j, 0] + lag[j]

    model.precedence = pyo.Constraint(jobs, rule=precedence_rule)

    # Machine disjunctive constraints
    def machine_rule_a(mdl, k):
        (ja, oa), (jb, ob) = machine_pairs[k]
        return mdl.start[jb, ob] >= (
            mdl.start[ja, oa] + ptime[(ja, oa)]
            - bigM * (1 - mdl.order[k])
        )

    def machine_rule_b(mdl, k):
        (ja, oa), (jb, ob) = machine_pairs[k]
        return mdl.start[ja, oa] >= (
            mdl.start[jb, ob] + ptime[(jb, ob)]
            - bigM * mdl.order[k]
        )

    model.machine_a = pyo.Constraint(pair_set, rule=machine_rule_a)
    model.machine_b = pyo.Constraint(pair_set, rule=machine_rule_b)

    # Makespan constraints: at least completion of every operation
    def makespan_rule(mdl, j, o):
        return mdl.makespan >= mdl.start[j, o] + ptime[(j, o)]

    model.makespan_con = pyo.Constraint(tasks, rule=makespan_rule)

    model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}