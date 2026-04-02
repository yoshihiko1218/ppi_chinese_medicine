#!/usr/bin/env python3
"""
Stage 5: PPI Network & Core Target Selection
- STRING API for protein-protein interactions
- NetworkX for topology analysis (Degree, Betweenness, Closeness)
- Visualization of PPI network
"""
import pandas as pd
import requests
import json
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
import os

os.makedirs("results/figures", exist_ok=True)
os.makedirs("results/tables", exist_ok=True)

# Load common targets
common = pd.read_csv("data/targets/common_targets.csv")
genes = common['gene_symbol'].tolist()
print(f"Common targets for PPI analysis: {len(genes)}")

# Query STRING API
print("\nQuerying STRING database...")
string_url = "https://string-db.org/api/json/network"
params = {
    "identifiers": "%0d".join(genes),
    "species": 9606,  # Homo sapiens
    "required_score": 400,  # confidence >= 0.4 (as in thesis)
    "caller_identity": "network_pharmacology_study"
}

r = requests.get(string_url, params=params, timeout=120)
print(f"STRING response: {r.status_code}, {len(r.text)} bytes")

if r.status_code == 200:
    interactions = r.json()
    print(f"Total interactions: {len(interactions)}")

    # Build NetworkX graph
    G = nx.Graph()
    G.add_nodes_from(genes)

    for edge in interactions:
        node1 = edge["preferredName_A"]
        node2 = edge["preferredName_B"]
        score = edge["score"]
        G.add_edge(node1, node2, weight=score)

    # Remove isolated nodes
    isolated = list(nx.isolates(G))
    G.remove_nodes_from(isolated)
    print(f"Removed {len(isolated)} isolated nodes: {isolated}")
    print(f"Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Topology analysis
    degree = dict(G.degree())
    betweenness = nx.betweenness_centrality(G)
    closeness = nx.closeness_centrality(G)

    # Create topology table
    topo_df = pd.DataFrame({
        "gene_symbol": list(degree.keys()),
        "Degree": list(degree.values()),
        "Betweenness": [betweenness[n] for n in degree.keys()],
        "Closeness": [closeness[n] for n in degree.keys()],
    })
    topo_df = topo_df.sort_values("Degree", ascending=False)
    topo_df.to_csv("results/tables/ppi_topology.csv", index=False)

    # Core targets: above-median Degree
    median_degree = topo_df['Degree'].median()
    core_targets = topo_df[topo_df['Degree'] >= median_degree].copy()
    core_targets.to_csv("results/tables/core_targets.csv", index=False)
    print(f"\nMedian Degree: {median_degree}")
    print(f"Core targets (Degree >= {median_degree}): {len(core_targets)}")
    print("\nTop 20 targets by Degree:")
    print(core_targets.head(20).to_string(index=False))

    # === PPI Network Visualization ===
    fig, ax = plt.subplots(figsize=(14, 14))

    # Layout
    pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)

    # Node sizes based on degree
    node_sizes = [degree[n] * 80 + 100 for n in G.nodes()]

    # Node colors based on degree
    degrees_list = [degree[n] for n in G.nodes()]
    norm = plt.Normalize(min(degrees_list), max(degrees_list))
    colors = cm.YlOrRd(norm(degrees_list))

    # Draw
    nx.draw_networkx_edges(G, pos, alpha=0.2, width=0.5, ax=ax)
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=colors, alpha=0.9, ax=ax)

    # Labels for high-degree nodes
    labels = {n: n for n in G.nodes() if degree[n] >= median_degree}
    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight='bold', ax=ax)

    ax.set_title('PPI Network of Common Drug-Disease Targets', fontsize=16, fontweight='bold')
    ax.axis('off')

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=cm.YlOrRd, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.5, label='Degree')

    plt.tight_layout()
    plt.savefig("results/figures/ppi_network.png", dpi=300, bbox_inches='tight')
    plt.savefig("results/figures/ppi_network.pdf", bbox_inches='tight')
    print("\nSaved: results/figures/ppi_network.png")

    # === Core PPI Network (high-degree nodes only) ===
    core_genes = set(core_targets['gene_symbol'].tolist())
    G_core = G.subgraph(core_genes).copy()

    fig, ax = plt.subplots(figsize=(10, 10))
    pos_core = nx.spring_layout(G_core, k=2, iterations=50, seed=42)

    core_degrees = [degree[n] for n in G_core.nodes()]
    core_sizes = [d * 100 + 200 for d in core_degrees]
    norm_core = plt.Normalize(min(core_degrees), max(core_degrees))
    core_colors = cm.YlOrRd(norm_core(core_degrees))

    nx.draw_networkx_edges(G_core, pos_core, alpha=0.3, width=1, ax=ax)
    nx.draw_networkx_nodes(G_core, pos_core, node_size=core_sizes, node_color=core_colors, alpha=0.9, ax=ax)
    nx.draw_networkx_labels(G_core, pos_core, font_size=9, font_weight='bold', ax=ax)

    ax.set_title('Core PPI Network (Hub Targets)', fontsize=16, fontweight='bold')
    ax.axis('off')

    sm2 = plt.cm.ScalarMappable(cmap=cm.YlOrRd, norm=norm_core)
    sm2.set_array([])
    plt.colorbar(sm2, ax=ax, shrink=0.5, label='Degree')

    plt.tight_layout()
    plt.savefig("results/figures/ppi_core_network.png", dpi=300, bbox_inches='tight')
    plt.savefig("results/figures/ppi_core_network.pdf", bbox_inches='tight')
    print("Saved: results/figures/ppi_core_network.png")

    # Save network data for potential Cytoscape import
    edge_list = []
    for u, v, d in G.edges(data=True):
        edge_list.append({"source": u, "target": v, "score": d.get("weight", 0)})
    pd.DataFrame(edge_list).to_csv("results/tables/ppi_edges.csv", index=False)
    print("Saved: results/tables/ppi_edges.csv (Cytoscape-compatible)")

else:
    print(f"STRING API error: {r.status_code}")
    print(r.text[:500])
