#!/usr/bin/env python
from rich import print
from pyvis.network import Network, Node
import networkx as nx
import random
import database as db
import itertools

from typer import Typer

IMPORTED = True

app = Typer()


colors = [
    "#C724B1",
    "#71DBD4",
    "#642F6C",
    "#58A7AF",
    "#B3B0C4",
    "#3A3A59",
    "#59CBE8",
    "#1E22AA",
    "#00BCE1",
]

OUTPUT_PATH = "/tmp"


OMIT_PLAYERS = ["BYOCTF_Automaton#7840"]


def make_net():
    net = Network(
        height="900px",
        width="100%",
        directed=True,
        notebook=False,
        select_menu=True,
        filter_menu=True,
        neighborhood_highlight=True,
        bgcolor="#414199",
        font_color="#E93CAC",
        cdn_resources="remote",
    )
    # net.show_buttons()
    net.show_buttons(filter_=["physics"])

    return net


# net.toggle_physics(False)


@app.command()
def all_reports():
    # players and teams
    nxGraph = nx.DiGraph()  # other types of graphs
    players()

    # challenge relationships
    nxGraph = nx.MultiDiGraph()  # other types of graphs
    challs()

    # inter-player tips

    trans(trans_type="tip")


@app.command()
def trans(trans_type: str = "tip", user: str | None = None):
    net = make_net()
    nxGraph = nx.MultiDiGraph()  # other types of graphs
    with db.db_session:
        # for player in db.select(u for u in db.User):
        bot = db.User.get(name="BYOCTF_Automaton#7840")
        if user != None:
            user = db.User.get(name=user)
            if user == None:
                print("user not found")
                return "user not found"

        trans: db.Transaction
        if trans_type in ["*", "all"]:
            all_trans = db.select(t for t in db.Transaction)[:]
        else:
            all_trans = db.select(t for t in db.Transaction if t.type == trans_type)[:]

        avg_trans = sum([t.value for t in all_trans]) / len(all_trans)
        # print(avg_trans)
        len_all_trans = len(all_trans)
        for trans in all_trans:
            if trans.value == 0: 
                print('invalid transaction', trans)
                continue
            if user != None:
                if user.id not in [trans.sender.id, trans.recipient.id]:
                    continue
            title = f"""
Num of sent transactions: {db.select(t for t in db.Transaction if t.sender == trans.sender ).count()}
Num of recv transactions: {db.select(t for t in db.Transaction if t.recipient == trans.sender ).count()}

			""".strip()
            # print(f'trans id {trans.id} - sender "{trans.sender.name}" recipient "{trans.recipient.name}" amount {trans.value}')
            nxGraph.add_node(trans.sender.name, title=title)
            nxGraph.add_edge(
                trans.sender.name,
                trans.recipient.name,
                weight=min(avg_trans / trans.value, 20),
                type=trans.type,
            )  # type: ignore

            # nxGraph.add_node(trans.sender.name, sender=trans.sender.name, )
            # nxGraph.add_node(trans.recipient.name, sender=trans.recipient.name)

    net.from_nx(nxGraph)
    # net.show_buttons()
    # net.filter_menu
    if IMPORTED:
        net.write_html("/tmp/trans_net.html")
        with open("/tmp/trans_net.html") as f:
            return f.read()
    net.show(
        f"{OUTPUT_PATH}/inter-player_transactions_{trans_type}.html", notebook=False
    )


@app.command()
def players():
    net = make_net()
    nxGraph = nx.MultiDiGraph()  # other types of graphs
    with db.db_session:
        all_teams = db.select(t for t in db.Team if t.name != "__botteam__")[:]
        len_all_teams = len(all_teams)
        avg_score = db.average_score()
        for idx, team in enumerate(all_teams):
            title = f"""
Team Name: {team.name}
Team ID: {team.id}
Team UUID: {team.uuid}
Team members: {', '.join([p.name for p in team.members])} 
			""".strip()
            nxGraph.add_node(
                team.name,
                size=25,
                color="#c1ae09",
                font="20px arial black",
                uuid=str(team.uuid),
                title=title,
            )
            for player in team.members:
                score = db.getScore(player)
                # print(player, score)
                nxGraph.add_node(
                    player.name,
                    size=max(max(score, 1) // max(score, 1), 10),
                    color=random.choice(colors),
                    group=idx,
                )
                nxGraph.add_edge(player.name, team.name)

    net.from_nx(nxGraph)
    # net.show_buttons()
    # net.filter_menu
    if IMPORTED:
        net.write_html("/tmp/players_net.html")
        with open("/tmp/players_net.html") as f:
            return f.read()
    net.show(f"{OUTPUT_PATH}/challenge_relationships.html", notebook=False)


@app.command()
def challs(chall: str | None = None):
    """chall is the uuid of the challenge"""
    net = make_net()
    nxGraph = nx.MultiDiGraph()  # other types of graphs
    with db.db_session:
        chall: db.Challenge
        if chall != None:
            filtering = True
            chall = db.Challenge.get(uuid=chall)
            if chall == None:
                print("challenge not found")
                return "challenge not found"
        if chall != None:
            challs = db.select(c for c in db.Challenge if c == chall)[:]
        else:
            challs = db.select(c for c in db.Challenge)[:]

        len_challs = len(challs)
        for idx, chall in enumerate(challs):
            title = f"""
Challenge Title: {chall.title}
Challenge ID: {chall.id}
Challenge UUID: {chall.uuid}
Challenge Author: {chall.author.name}
Number of flags: {len(chall.flags)}

			""".strip()
            relations = 0

            relations += len(chall.children)
            relations += len(chall.parent)

            color = colors[relations % len(colors)]  # Example logic

            nxGraph.add_node(
                chall.title,
                label=f"{chall.title}",
                color=color,
                author=chall.author.name,
                title=title,
                group=idx,
            )

            for parent in chall.parent:
                nxGraph.add_node(parent.title, label=parent.title, group=idx)
                nxGraph.add_edge(
                    parent.title, chall.title, weight=relations / len_challs
                )  # this is the correct way to express child parent relationships ; test by dev reset and looking at the relationship of small number of challs

    net.from_nx(nxGraph)
    # net.show_buttons()
    # net.filter_menu
    if IMPORTED:
        net.write_html("/tmp/challs_net.html")
        with open("/tmp/challs_net.html") as f:
            return f.read()
    net.show(f"{OUTPUT_PATH}/players_and_teams.html", notebook=False)


if __name__ == "__main__":
    # IMPORTED = False
    net = make_net()
    app()
