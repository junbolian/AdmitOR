def solve(params):
    import pyomo.environ as pyo
    from pyomo.contrib.appsi.solvers.highs import Highs

    # ---------- read numeric parameters ----------
    N = 9
    # distance matrix D[i][j]
    D = [[0.0] * N for _ in range(N)]

    # symmetric off-diagonal pairs (i<j), skip the asymmetric pair (2,4)
    sym_pairs = {}
    for i in range(N):
        for j in range(i + 1, N):
            if (i, j) == (2, 4) or (i, j) == (4, 2):
                continue
            sym_pairs[(i, j)] = params["dist_%d_%d" % (i, j)]

    D[2][4] = params["dist_2_4_asym"]
    D[4][2] = params["dist_4_2_asym"]
    for (i, j), v in sym_pairs.items():
        D[i][j] = float(v)
        D[j][i] = float(v)

    # ---------- structural data ----------
    required_pairs = [(0, 3), (1, 7), (2, 8), (3, 7), (4, 5), (4, 6), (5, 7), (5, 8)]
    # directed service arcs: both orientations for each required edge
    service_arcs = []
    for (u, v) in required_pairs:
        service_arcs.append((u, v))
        service_arcs.append((v, u))
    service_set = set(service_arcs)

    # all ordered pairs used as transit (complete digraph, no self loops)
    all_arcs = [(i, j) for i in range(N) for j in range(N) if i != j]

    nodes = list(range(N))

    # ---------- model ----------
    model = pyo.ConcreteModel()

    model.SERVICE = pyo.Set(initialize=service_arcs, dimen=2)
    model.ARC = pyo.Set(initialize=all_arcs, dimen=2)

    # service selection (binary): ==1 means this directed service arc is traversed as service
    model.x = pyo.Var(model.SERVICE, domain=pyo.Binary)
    # transit multiplicity on each ordered pair
    # upper bound: total required edges = 8, a reasonable bound is 8
    U = len(required_pairs)
    model.y = pyo.Var(model.ARC, domain=pyo.NonNegativeIntegers, bounds=(0, U))

    # ----- constraint: each required edge serviced at least once (either orientation) -----
    model.service_req = pyo.ConstraintList()
    for (u, v) in required_pairs:
        model.service_req.add(model.x[u, v] + model.x[v, u] >= 1)

    # ----- flow balance at every node -----
    # net outgoing (service + transit) == net incoming
    def balance_rule(m, k):
        out_terms = []
        in_terms = []
        for j in nodes:
            if j == k:
                continue
            # transit out
            out_terms.append(m.y[k, j])
            # transit in
            in_terms.append(m.y[j, k])
        # service arcs
        for (a, b) in service_arcs:
            if a == k:
                out_terms.append(m.x[a, b])
            if b == k:
                in_terms.append(m.x[a, b])
        return sum(out_terms) - sum(in_terms) == 0

    model.balance = pyo.Constraint(nodes, rule=balance_rule)

    # ----- connectivity / subtour elimination via single-commodity flow -----
    # Introduce flow on the same arcs (service = 1 unit min, transit = >=0) rooted at depot 0.
    # Standard: each non-depot node consumes 1 unit of flow; depot is source.
    # This forces the whole selected multigraph connected to depot.
    # Flow arcs: use same ARC set with continuous flow variables.
    model.f = pyo.Var(model.ARC, domain=pyo.NonNegativeReals)

    # capacity linking: flow on arc <= (N-1) * (x_or_y capacity indicator)
    # capacity for transit arc (i,j): y_{ij} + (1 if service selected) ... need to account service flows.
    # Use cap = U * (y[i,j] + sum of service arcs (i,j) indicator).
    # service arc (i,j) is a directed arc; combine capacity.
    def cap_rule(m, i, j):
        # arc-capacity variable expressed in terms of y and x
        transit = m.y[i, j]
        serv = 0
        if (i, j) in service_set:
            serv = m.x[i, j]
        # max flow through this arc
        return m.f[i, j] <= (N) * (transit + serv)

    model.cap = pyo.Constraint(model.ARC, rule=cap_rule)

    # flow conservation: depot sends (N-1) units, every other node consumes 1
    def flow_balance_rule(m, k):
        out_terms = [m.f[k, j] for j in nodes if j != k]
        in_terms = [m.f[j, k] for j in nodes if j != k]
        if k == 0:
            return sum(out_terms) - sum(in_terms) == (N - 1)
        else:
            return sum(in_terms) - sum(out_terms) == 1

    model.flow_balance = pyo.Constraint(nodes, rule=flow_balance_rule)

    # ----- objective: minimize total travel distance -----
    def obj_rule(m):
        total = 0
        for (i, j) in service_arcs:
            total += D[i][j] * m.x[i, j]
        for (i, j) in all_arcs:
            total += D[i][j] * m.y[i, j]
        return total

    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # ---------- solve ----------
    solver = Highs()
    solver.solve(model)
    obj_val = float(pyo.value(model.objective))
    return {'objective': obj_val, 'status': 'optimal'}