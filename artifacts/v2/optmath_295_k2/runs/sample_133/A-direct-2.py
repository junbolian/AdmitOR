import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Structural constants
    num_nodes = 5
    nodes = list(range(num_nodes))
    pairs = [(i, j) for i in range(num_nodes) for j in range(i + 1, num_nodes)]

    # Distance lookup (read from params)
    dist_map = {
        (0, 1): params["distance_01"],
        (0, 2): params["distance_02"],
        (0, 3): params["distance_03"],
        (0, 4): params["distance_04"],
        (1, 2): params["distance_12"],
        (1, 3): params["distance_13"],
        (1, 4): params["distance_14"],
        (2, 3): params["distance_23"],
        (2, 4): params["distance_24"],
        (3, 4): params["distance_34"],
    }

    n_select = params["num_facilities_to_select"]
    M = params["large_constant_M"]

    m = pyo.ConcreteModel()

    # Decision variables
    m.x = pyo.Var(nodes, domain=pyo.Binary)
    m.y = pyo.Var(pairs, domain=pyo.Binary)
    m.z = pyo.Var(domain=pyo.NonNegativeReals)  # minimum distance

    # Select exactly n facilities
    m.select_con = pyo.Constraint(
        expr=sum(m.x[i] for i in nodes) == n_select
    )

    # Pairwise linking constraints
    def pair_lb_rule(m, i, j):
        return m.y[i, j] <= m.x[i]

    def pair_lb2_rule(m, i, j):
        return m.y[i, j] <= m.x[j]

    def pair_ub_rule(m, i, j):
        return m.y[i, j] >= m.x[i] + m.x[j] - 1

    m.pair_lb = pyo.Constraint(pairs, rule=pair_lb_rule)
    m.pair_lb2 = pyo.Constraint(pairs, rule=pair_lb2_rule)
    m.pair_ub = pyo.Constraint(pairs, rule=pair_ub_rule)

    # Big-M distance constraints: z + M * y_ij <= M + dist_ij  (relaxed when y=0)
    def dist_rule(m, i, j):
        return m.z + M * m.y[i, j] <= M + dist_map[(i, j)]

    m.dist_con = pyo.Constraint(pairs, rule=dist_rule)

    # Objective: maximize minimum distance
    m.obj = pyo.Objective(expr=m.z, sense=pyo.maximize)

    # Solve with HiGHS
    Highs().solve(m)

    obj_val = float(pyo.value(m.obj))
    return {"objective": obj_val, "status": "optimal"}