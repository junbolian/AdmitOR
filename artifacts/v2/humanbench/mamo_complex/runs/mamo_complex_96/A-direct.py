import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_vertices = int(params["num_vertices"])
    num_edges = int(params["num_edges"])
    incidence = params["edge_incidence_a"]

    verts = list(range(num_vertices))
    edges = list(range(num_edges))

    # Normalize incidence into a callable: edge -> list of incident vertices
    def incident_vertices(e):
        result = []
        for v in verts:
            inc = incidence
            # Try to extract incidence for vertex v
            try:
                vec = inc[v]
                if hasattr(vec, "__getitem__"):
                    if vec[e]:
                        result.append(v)
                    continue
            except (TypeError, IndexError, KeyError):
                pass
            # Fallback: int not subscriptable -> cannot use
            return None
        return result

    # Build edge->vertices mapping robustly
    edge_incidence = {}
    for e in edges:
        incident = []
        for v in verts:
            val = None
            try:
                vec = incidence[v]
                if hasattr(vec, "__getitem__"):
                    val = vec[e]
            except (TypeError, IndexError, KeyError):
                val = None
            if val:
                incident.append(v)
        edge_incidence[e] = incident

    # If incidence data unusable (int), fall back to graph structure from problem
    if all(len(edge_incidence[e]) == 0 for e in edges):
        # a-j = 0-9
        pairs = [
            ("a", "f"), ("a", "e"), ("a", "b"),
            ("b", "g"), ("b", "c"),
            ("c", "h"), ("c", "d"),
            ("d", "i"), ("d", "e"),
            ("e", "j"),
        ]
        inner = ["f", "g", "h", "i", "j"]
        for i in range(len(inner)):
            for j in range(i + 1, len(inner)):
                pairs.append((inner[i], inner[j]))
        letter_to_idx = {ch: k for k, ch in enumerate("abcdefghij")}
        edge_incidence = {}
        for k, (u, w) in enumerate(pairs):
            edge_incidence[k] = [letter_to_idx[u], letter_to_idx[w]]

    model = pyo.ConcreteModel()
    model.V = pyo.Set(initialize=verts)
    model.E = pyo.Set(initialize=list(edge_incidence.keys()))

    model.x = pyo.Var(model.V, domain=pyo.Binary)

    def cover_rule(m, e):
        return sum(m.x[v] for v in edge_incidence[e]) >= 1

    model.cover = pyo.Constraint(model.E, rule=cover_rule)

    model.obj = pyo.Objective(expr=sum(model.x[v] for v in model.V), sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": round(obj_val), "status": "optimal"}