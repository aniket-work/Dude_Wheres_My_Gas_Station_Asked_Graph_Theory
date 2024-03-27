import networkx as nx
import random
from pyvis.network import Network
import webbrowser
from neo4j import GraphDatabase

# Neo4j connection parameters
uri = "bolt://localhost:7687"
user = "neo4j"
password = "abcd1234"


# Create a graph object
G = nx.DiGraph()  # Use a directed graph

# Define node types
node_types = ['residence', 'office', 'holiday', 'intersection']

# Add nodes with different types
num_residences = 100
num_offices = 20
num_holidays = 10
num_intersections = 15

residences = [f'Residence {i}' for i in range(num_residences)]
offices = [f'Office {i}' for i in range(num_offices)]
holidays = [f'Holiday {i}' for i in range(num_holidays)]
intersections = [f'Intersection {i}' for i in range(num_intersections)]

for node in residences:
    G.add_node(node, type='residence')

for node in offices:
    G.add_node(node, type='office')

for node in holidays:
    G.add_node(node, type='holiday')

for node in intersections:
    G.add_node(node, type='intersection')

# Connect residences to offices, holidays, and intersections
for residence in residences:
    office_connection = random.choice(offices)
    holiday_connection = random.choice(holidays)
    intersection_connections = random.sample(intersections, 2)

    # Connect residence to office
    random_intersection = random.choice(intersection_connections)
    G.add_edge(residence, random_intersection, type='drives')
    G.add_edge(random_intersection, office_connection, type='drives')

    # Connect residence to holiday
    random_intersection = random.choice(intersection_connections)
    G.add_edge(residence, random_intersection, type='drives')
    G.add_edge(random_intersection, holiday_connection, type='drives')

# Visualize the graph with PyVis
net = Network(height='750px', width='100%', bgcolor='#222222', font_color='white')
net.barnes_hut(gravity=-80000, central_gravity=0.3, spring_length=100, spring_strength=0.001)

# Set node properties based on type
node_color_map = {
    'residence': 'green',
    'office': 'blue',
    'holiday': 'orange',
    'intersection': 'red'
}

for node in G.nodes(data=True):
    net.add_node(node[0], label=node[0], color=node_color_map[node[1]['type']], title=node[1]['type'])

# Add edges
for edge in G.edges(data=True):
    net.add_edge(edge[0], edge[1], title=edge[2]['type'], arrows='to')

# Save the graph to an HTML file
graph_html_file = 'graph.html'
net.save_graph(graph_html_file)
print(f"Graph exported to '{graph_html_file}'")

# Open the HTML file in a web browser
webbrowser.open_new_tab(graph_html_file)


def run_betweenness_algo():
    driver = GraphDatabase.driver(uri, auth=(user,password))

    query_project_graph = """
        CALL gds.graph.project('gasStationGraph', ['Residence', 'Office', 'Holiday', 'Intersection'], {DRIVES: {properties: 'weight'}})
    """
    query_betweenness_algo = """
       CALL gds.betweenness.stream('gasStationGraph')
        YIELD nodeId, score
        WITH nodeId, score, labels(gds.util.asNode(nodeId)) AS nodeLabelsList
        WHERE 'Intersection' IN nodeLabelsList
        RETURN gds.util.asNode(nodeId).name as name, score
        ORDER BY score DESC
    """
    with driver.session() as session:
        # Delete any existing projected graph
        session.run("CALL gds.graph.drop('gasStationGraph', false)")

        # Create the graph for topological sorting
        session.run(query_project_graph)

        # Execute topological sort algorithm and calculate distance from source
        result = session.run(query_betweenness_algo)

        # Print sorted sequence of courses with maxDistanceFromSource
        print("Betweenness Algorith Score :")
        for record in result:
            name = record['name']
            print(f"Intersection: {name}, has centrality in this city network as : {record['score']}")
    # Close the driver
    driver.close()


def networkx_to_neo4j(G, uri, user, password):
    # Create a Neo4j driver instance
    driver = GraphDatabase.driver(uri, auth=(user, password))

    # Create a session
    with driver.session() as session:
        # Clear the existing nodes and relationships in Neo4j
        session.run("MATCH (n) DETACH DELETE n")

        # Create nodes in Neo4j
        for node, node_data in G.nodes(data=True):
            node_type = node_data['type']
            node_label = node_type.capitalize()
            query = f"CREATE (n:{node_label} {{name: $name}})"
            session.run(query, name=node)

        # Create relationships in Neo4j
        for source, target, edge_data in G.edges(data=True):
            edge_type = edge_data['type']
            query = "MATCH (a), (b) WHERE a.name = $source AND b.name = $target MERGE (a)-[r:DRIVES]->(b)"
            session.run(query, source=source, target=target)

    # Close the driver
    driver.close()


def main():
    # Call the function to convert the NetworkX graph to Neo4j
    networkx_to_neo4j(G, uri, user, password)

    run_betweenness_algo()



if __name__ == "__main__":
    main()

