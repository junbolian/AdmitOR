import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_slots = params["num_slots"]
    num_brands = params["num_brands"]
    adjacency_links = params["adjacency_links"]
    allowed_brands_per_slot = params["allowed_brands_per_slot"]

    slots = list(range(num_slots))
    brands = list(range(num_brands))

    # Normalize allowed brands per slot into a dict of lists/sets
    allowed = {}
    for s in slots:
        allowed[s] = set(allowed_brands_per_slot[s])

    # Undirected edges (deduplicate, ignore self-loops)
    edges = set()
    for a, b in adjacency_links:
        if a == b:
            continue
        edges.add((min(a, b), max(a, b)))

    model = pyo.ConcreteModel()

    model.SLOTS = pyo.Set(initialize=slots)
    model.BRANDS = pyo.Set(initialize=brands)
    model.EDGES = pyo.Set(initialize=list(edges), dimen=2)

    # Feasible (slot, brand) combinations
    combos = [(s, b) for s in slots for b in brands if b in allowed[s]]
    model.ALLOWED = pyo.Set(initialize=combos, dimen=2)

    model.assign = pyo.Var(model.ALLOWED, domain=pyo.Binary)

    # Each slot gets exactly one allowed brand
    def one_brand_rule(m, s):
        return sum(m.assign[s, b] for b in brands if (s, b) in combos) == 1

    model.one_brand = pyo.Constraint(model.SLOTS, rule=one_brand_rule)

    # Adjacent slots must differ
    def differ_rule(m, i, j):
        return sum(m.assign[i, b] for b in brands if (i, b) in combos) + \
               sum(m.assign[j, b] for b in brands if (j, b) in combos) >= 0

    # Distinctness: for each edge and each brand, sum of assignments <= 1
    def edge_brand_rule(m, i, j, b):
        terms = []
        if (i, b) in combos:
            terms.append(m.assign[i, b])
        if (j, b) in combos:
            terms.append(m.assign[j, b])
        if not terms:
            return pyo.Constraint.Skip
        return sum(terms) <= 1

    model.edge_brand = pyo.Constraint(
        [(i, j, b) for (i, j) in edges for b in brands],
        rule=edge_brand_rule,
    )

    # Objective variable M = max brand used
    model.max_brand = pyo.Var(domain=pyo.NonNegativeReals)

    def max_brand_lb_rule(m, b):
        terms = [m.assign[s, b] for s in slots if (s, b) in combos]
        if not terms:
            return pyo.Constraint.Skip
        return m.max_brand >= b * sum(terms)

    model.max_brand_lb = pyo.Constraint(model.BRANDS, rule=max_brand_lb_rule)

    def max_brand_ub_rule(m):
        terms = []
        for (s, b) in combos:
            terms.append(b * m.assign[s, b])
        if not terms:
            return pyo.Constraint.Skip
        return m.max_brand <= sum(terms)

    model.max_brand_ub = pyo.Constraint(rule=max_brand_ub_rule)

    model.objective = pyo.Objective(expr=model.max_brand, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.objective))

    return {"objective": obj_val, "status": "optimal"}