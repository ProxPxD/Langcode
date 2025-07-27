from rdflib import Graph
from pathlib import Path

p_sandbox = Path('/home/proxpxd/Desktop/rdf-sandbox')
p_db = p_sandbox / 'db'

g = Graph()

g.parse(p_db)

query = """
    SELECT ?s ?p ?o WHERE {
        ?s ?p ?o
    }
"""

print(g.query(query))
