import os
import matplotlib.pyplot as plt
import networkx as nx
from dotenv import load_dotenv
from supabase import create_client

event_name = "JMM 2026"

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

items = supabase.table("items").select("id, song").eq("event", event_name).execute().data
item_ids = [item["id"] for item in items]

players = (
    supabase.table("players")
    .select("item_id, telegram_handle")
    .in_("item_id", item_ids)
    .execute()
    .data
)

handles = {row["telegram_handle"] for row in players}
members = supabase.table("members").select("telegram_handle, name").in_("telegram_handle", list(handles)).execute().data
names = {row["telegram_handle"]: row["name"] for row in members}

graph = nx.Graph()
for item in items:
    song = item["song"]
    song_players = list({row["telegram_handle"] for row in players if row["item_id"] == item["id"]})

    for i in range(len(song_players)):
        for j in range(i + 1, len(song_players)):
            a, b = song_players[i], song_players[j]
            if graph.has_edge(a, b):
                graph[a][b]["weight"] += 1
            else:
                graph.add_edge(a, b, weight=1)

labels = {handle: names.get(handle, handle) for handle in graph.nodes}

components = sorted(nx.connected_components(graph), key=len, reverse=True)
widths = [max(len(component) ** 0.5, 1) for component in components]

fig, axes = plt.subplots(1, len(components), figsize=(20, 12), gridspec_kw={"width_ratios": widths})
if len(components) == 1:
    axes = [axes]

for ax, component in zip(axes, components):
    subgraph = graph.subgraph(component)
    sub_weights = [subgraph[a][b]["weight"] for a, b in subgraph.edges]
    pos = nx.spring_layout(subgraph, seed=0, k=3 / len(component) ** 0.5, iterations=200)

    nx.draw_networkx_nodes(subgraph, pos, node_color="#2a78d6", node_size=250, ax=ax)
    nx.draw_networkx_edges(subgraph, pos, width=sub_weights, alpha=0.4, ax=ax)
    sub_labels = {node: labels[node] for node in component}
    nx.draw_networkx_labels(
        subgraph, pos, sub_labels, font_size=7, ax=ax,
        bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.7, "pad": 0},
    )
    ax.axis("off")

fig.suptitle(f"Player connections - {event_name}")
fig.tight_layout()
fig.savefig("player_connections.png", dpi=200, bbox_inches="tight")
plt.show()
