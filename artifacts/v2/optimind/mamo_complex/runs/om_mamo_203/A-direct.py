def solve(params):
    import pyomo.environ as pyo
    from pyomo.contrib.appsi.solvers.highs import Highs

    edge_capacities = params["edge_capacities"]
    num_cities = int(params["num_cities"])

    # Number of other cities each row connects to (all cities except itself)
    per_row = num_cities - 1

    # Build directed edge list. The problem text lists every ordered pair (i, j)
    # with i != j, row by row, so the flattened list maps directly to these pairs.
    edges = []
    idx = 0
    for i in range(num_cities):
        for j in range(num_cities):
            if i == j:
                continue
            cap = edge_capacities[idx]
            idx += 1
            edges.append((i, j, cap))

    model = pyo.ConcreteModel()
    model.edges = pyo.Set(initialize=[(i, j) for (i, j, c) in edges], dimen=2)

    cap_dict = {(i, j): c for (i, j, c) in edges}
    model.cap = pyo.Param(model.edges, initialize=cap_dict, mutable=True)

    source = 0
    sink = num_cities - 1

    def flow_bounds(m, i, j):
        return (0, m.cap[i, j])
    model.flow = pyo.Var(model.edges, bounds=flow_bounds)

    def flow_balance(m, k):
        inflow = sum(m.flow[i, j] for (i, j) in m.edges if j == k)
        outflow = sum(m.flow[i, j] for (i, j) in m.edges if i == k)
        if k == source:
            return outflow - inflow >= 0
        elif k == sink:
            return inflow - outflow >= 0
        else:
            return outflow - inflow == 0
    model.balance = pyo.Constraint(range(num_cities), rule=flow_balance)

    model.total_flow = pyo.Expression(
        expr=sum(model.flow[i, j] for (i, j) in model.edges if j == sink)
    )

    model.obj = pyo.Objective(expr=model.total_flow, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}