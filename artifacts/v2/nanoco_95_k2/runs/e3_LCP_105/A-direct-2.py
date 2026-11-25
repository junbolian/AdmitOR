import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_slots = params["num_slots"]
    num_brands = params["num_brands"]
    adjacency_links = params["adjacency_links"]
    allowed_brands_per_slot = params["allowed_brands_per_slot"]

    slots = list(range(num_slots))
    brands = list(range(num_brands))

    allowed = {i: list(allowed_brands_per_slot[i]) for i in slots}

    model = pyo.ConcreteModel()

    model.x = pyo.Var(slots, brands, domain=pyo.Binary)
    model.z = pyo.Var(domain=pyo.NonNegativeReals)

    def assign_rule(m, i):
        return sum(m.x[i, j] for j in allowed[i]) == 1

    model.assign_con = pyo.Constraint(slots, rule=assign_rule)

    def restrict_rule(m, i, j):
        if j not in allowed[i]:
            return m.x[i, j] == 0
        return pyo.Constraint.Skip

    model.restrict_con = pyo.Constraint(slots, brands, rule=restrict_rule)

    def assign_value_expr(m, i, j):
        return sum(j * m.x[i, j] for j in allowed[i])

    # Adjacency: distinct brands -> use big-M style linear inequality via auxiliaries
    pair_index = [(a, b) for (a, b) in adjacency_links if a != b]

    def adj_rule(m, a, b):
        val_a = sum(j * m.x[a, j] for j in allowed[a])
        val_b = sum(j * m.x[b, j] for j in allowed[b])
        return val_a - val_b >= 1 - num_brands * m.disc[(a, b)]

    # create a distinctness slack per pair
    model.disc = pyo.Var(pair_index, domain=pyo.Binary)

    def adj_rule_b(m, a, b):
        val_a = sum(j * m.x[a, j] for j in allowed[a])
        val_b = sum(j * m.x[b, j] for j in allowed[b])
        return val_b - val_a >= 1 - num_brands * (1 - m.disc[(a, b)])

    model.adj_con_gt = pyo.Constraint(pair_index, rule=adj_rule)
    model.adj_con_lt = pyo.Constraint(pair_index, rule=adj_rule_b)

    def z_rule(m, i, j):
        return j * m.x[i, j] <= m.z

    model.z_con = pyo.Constraint(slots, brands, rule=z_rule)

    model.obj = pyo.Objective(expr=model.z, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}