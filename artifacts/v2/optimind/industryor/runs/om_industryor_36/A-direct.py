import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Processing times t[i][j] with i in 1..3 (products), j in 1..3 (machines)
    t = {
        (1, 1): params["t_11"], (1, 2): params["t_12"], (1, 3): params["t_13"],
        (2, 1): params["t_21"], (2, 2): params["t_22"], (2, 3): params["t_23"],
        (3, 1): params["t_31"], (3, 2): params["t_32"], (3, 3): params["t_33"],
    }

    products = [1, 2, 3]
    machines = [1, 2, 3]

    model = pyo.ConcreteModel()

    # Position of product i in the common permutation (1..3)
    model.pos = pyo.Var(products, domain=pyo.RangeSet(1, 3))
    model.pos_is_1 = pyo.Var(products, domain=pyo.Binary)
    model.pos_is_2 = pyo.Var(products, domain=pyo.Binary)
    model.pos_is_3 = pyo.Var(products, domain=pyo.Binary)

    # Assign each product a distinct position
    model.assign = pyo.ConstraintList()
    for i in products:
        model.assign.add(model.pos_is_1[i] + model.pos_is_2[i] + model.pos_is_3[i] == 1)
        model.assign.add(model.pos[i] == 1 * model.pos_is_1[i] + 2 * model.pos_is_2[i] + 3 * model.pos_is_3[i])
    model.assign.add(sum(model.pos_is_1[i] for i in products) == 1)
    model.assign.add(sum(model.pos_is_2[i] for i in products) == 1)
    model.assign.add(sum(model.pos_is_3[i] for i in products) == 1)

    # Start time of product i on machine j
    model.start = pyo.Var(products, machines, domain=pyo.NonNegativeReals)
    # Completion time (cycle time) variable
    model.C = pyo.Var(domain=pyo.NonNegativeReals)
    # Makespan upper bound that is minimized
    model.T = pyo.Var(domain=pyo.NonNegativeReals)

    # Disjunctive big-M constraints for machine ordering
    def make_bigM():
        total = sum(t[(i, j)] for i in products for j in machines)
        return total + 1

    bigM = make_bigM()

    # New boolean y[i,k]: 1 if product i precedes product k in the common order
    # We derive it from positions using a big-M comparison on positions.
    model.y = pyo.Var(products, products, domain=pyo.Binary)

    model.order = pyo.ConstraintList()
    for i in products:
        for k in products:
            if i == k:
                continue
            # y[i,k] == 1 iff pos[i] < pos[k]
            model.order.add(model.pos[i] - model.pos[k] <= bigM * (1 - model.y[i, k]) - 1)
            model.order.add(model.pos[i] - model.pos[k] >= -bigM * model.y[i, k] + 1)

    # Precedence within a product across machines
    model.preced = pyo.ConstraintList()
    for i in products:
        for j in machines[:-1]:
            model.preced.add(model.start[i, j + 1] >= model.start[i, j] + t[(i, j)])

    # No overlap on each machine, respecting the common order
    model.machine = pyo.ConstraintList()
    for j in machines:
        for i in products:
            for k in products:
                if i == k:
                    continue
                model.machine.add(
                    model.start[i, j] + t[(i, j)] <= model.start[k, j] + bigM * (1 - model.y[i, k])
                )

    # Cycle time: completion of last operations; enforce C >= every completion
    model.cycle = pyo.ConstraintList()
    for i in products:
        model.cycle.add(model.start[i, 3] + t[(i, 3)] <= model.C)

    # Objective: minimize cycle time
    model.obj = pyo.Objective(expr=model.C, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}