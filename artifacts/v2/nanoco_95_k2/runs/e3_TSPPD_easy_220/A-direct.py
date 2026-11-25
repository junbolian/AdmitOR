import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    dist = params["distance_matrix"]
    pairs = params["pickup_delivery_pairs"]
    n = params["num_nodes"]

    branch = list(range(1, n))
    positions = list(range(1, n))

    model = pyo.ConcreteModel()

    model.NODES = pyo.Set(initialize=branch)
    model.POS = pyo.Set(initialize=positions)

    # x[i, p] = 1 if branch node i is at tour position p
    model.x = pyo.Var(model.NODES, model.POS, domain=pyo.Binary)

    # y[i, j, p] = 1 if edge (i -> j) is traversed leaving position p (p in POS),
    # where node at position p is i and node at position p+1 (or depot if p == n-1) is j.
    # To keep it linear/quadratic-free, introduce flow-style edge vars between
    # consecutive positions in an aggregated form using node-position link vars.

    # Each branch node assigned exactly one position
    model.assign_node = pyo.Constraint(
        model.NODES,
        rule=lambda mm, i: sum(mm.x[i, p] for p in mm.POS) == 1,
    )
    # Each position holds exactly one node
    model.assign_pos = pyo.Constraint(
        model.POS,
        rule=lambda mm, p: sum(mm.x[i, p] for i in mm.NODES) == 1,
    )

    # Precedence: position(u) < position(v)
    for idx, (u, v) in enumerate(pairs):
        pu = sum(p * model.x[u, p] for p in model.POS)
        pv = sum(p * model.x[v, p] for p in model.POS)
        model.add_component(
            f"prec_{idx}", pyo.Constraint(expr=pu + 1 <= pv)
        )

    # Edge indicator: z[i, j, p] = 1 if i at pos p and j at pos p+1 (j=0 means depot end)
    # Use x-based bilinear would be quadratic; instead define z with linear linking.
    # z indexed by (i, j, p) for p in 1..n-2 plus special end p = n-1 to depot.
    next_nodes = branch + [0]
    model.EDGE_I = pyo.Set(initialize=branch)
    model.EDGE_J = pyo.Set(initialize=next_nodes)

    # Build z only for valid (i, j, p) combos. For p = n-1, j must be 0.
    valid_triples = []
    for p in positions:
        for i in branch:
            for j in next_nodes:
                if p == n - 1:
                    if j == 0:
                        valid_triples.append((i, j, p))
                else:
                    if j != 0:
                        valid_triples.append((i, j, p))

    model.TRIPLES = pyo.Set(initialize=valid_triples, dimen=3)
    model.z = pyo.Var(model.TRIPLES, domain=pyo.Binary)

    # z[i,j,p] = x[i,p] * x[j,p+1] via linking constraints using linearization:
    # z <= x[i,p]; z <= x[j,p+1]; z >= x[i,p] + x[j,p+1] - 1
    # Since each position has exactly one node, we can instead link z through sums.

    # Simpler: express objective directly and link z as arc selection.
    # For each position p and node i: sum_j z[i,j,p] == x[i,p]
    def outflow_rule(mm, i, p):
        return sum(mm.z[i, j, p] for j in next_nodes if (i, j, p) in valid_triples) == mm.x[i, p]
    model.outflow = pyo.Constraint(
        [(i, p) for i in branch for p in positions], rule=outflow_rule
    )

    # For each position p (p>=2) and node j: sum_i z[i,j,p-1] == x[j,p]
    def inflow_rule(mm, j, p):
        return sum(mm.z[i, j, p - 1] for i in branch if (i, j, p - 1) in valid_triples) == mm.x[j, p]
    model.inflow = pyo.Constraint(
        [(j, p) for j in branch for p in positions if p >= 2], rule=inflow_rule
    )

    # Depot departure: sum_j z[0-style] -- need departure from depot to pos 1
    # Introduce start arcs: s[j] = 1 if node j at position 1
    # sum_i z[i, j, 0] doesn't exist; instead inflow at pos 1 comes from depot.
    # Depot -> pos1 cost handled separately; ensure pos-1 node has no incoming z (p=1 inflow from depot).
    # pos1 inflow handled: for p=1, x[j,1] is set; departures from depot to every pos-1 node.

    # Objective
    obj_terms = []
    # Depot -> first node
    obj_terms.append(sum(dist[0][j] * model.x[j, 1] for j in branch))
    # Between consecutive positions
    obj_terms.append(
        sum(dist[i][j] * model.z[i, j, p] for (i, j, p) in valid_triples)
    )
    model.total_cost = pyo.Objective(expr=sum(obj_terms), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}