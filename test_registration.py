#!/usr/bin/env python3
"""Smoke test for self-service registration.

Run against a throwaway sqlite file — it will not touch byoctf.db:

    BYOCTF_TEST_DB=/tmp/regtest.db python3 test_registration.py

The property that actually matters is the last one. You cannot submit a flag
authored by someone on your own team, so if registration parks everybody in a
shared team then nobody can solve anybody's challenge — silently. Every other
check here is in service of that one.
"""
import os
import sys
import uuid

TEST_DB = os.environ.get("BYOCTF_TEST_DB", "/tmp/byoctf_regtest.db")
if os.path.exists(TEST_DB):
    os.remove(TEST_DB)

from settings import SETTINGS  # noqa: E402

SETTINGS["_db_type"] = "sqlite"
SETTINGS["_db_database"] = TEST_DB
SETTINGS["_debug"] = False

import database as db  # noqa: E402

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + (("  -- " + detail) if detail and not cond else ""))


@db.db_session
def seed():
    if db.Team.get(name="__unaffiliated__") is None:
        db.Team(name="__unaffiliated__", password="x" * 64)
    if db.User.get(name=SETTINGS["_botusername"]) is None:
        bot = db.User(name=SETTINGS["_botusername"], team=db.Team.get(name="__unaffiliated__"))
        db.rotate_player_keys(bot)
    db.commit()


@db.db_session
def test_quickreg_shape():
    print("\nquickreg")
    u = db.create_solo_player("alice")
    check("returns a User", not isinstance(u, str), repr(u))
    check("gets its own team", u.team.name == "alice", u.team.name)
    check("team has exactly one member", len(u.team.members) == 1)
    check("not parked in __unaffiliated__", u.team.name != "__unaffiliated__")
    check("has an api_key", bool(u.api_key))


@db.db_session
def test_rejections():
    print("\nrejections")
    check("duplicate handle rejected", isinstance(db.create_solo_player("alice"), str))
    check("too short rejected", isinstance(db.create_solo_player("ab"), str))
    check("too long rejected", isinstance(db.create_solo_player("z" * 33), str))
    check("spaces rejected", isinstance(db.create_solo_player("two words"), str))
    check("html rejected", isinstance(db.create_solo_player("<script>"), str))
    check("__unaffiliated__ reserved", isinstance(db.create_solo_player("__unaffiliated__"), str))


@db.db_session
def test_google_path():
    print("\ngoogle path")
    u = db.get_or_create_user_by_email("Jane.Smith@example.com")
    check("no real name on the board", "jane" not in u.name.lower(), u.name)
    check("gets its own team", u.team.name != "__unaffiliated__", u.team.name)
    same = db.get_or_create_user_by_email("jane.smith@EXAMPLE.com")
    check("same address returns same user (case-insensitive)", same.name == u.name)
    other = db.get_or_create_user_by_email("someone.else@example.com")
    check("different address, different team", other.team.name != u.team.name)


@db.db_session
def test_cross_team_solve():
    """The one that matters."""
    print("\ncross-team solve (the point of all this)")
    author = db.create_solo_player("author_bob")
    solver = db.create_solo_player("solver_carol")
    db.commit()

    check("author and solver are on different teams", author.team.name != solver.team.name)

    chall = db.Challenge(title="regtest-" + uuid.uuid4().hex[:6], description="d",
                         author=author, uuid=str(uuid.uuid4()), byoc=True)
    flag = db.Flag(flag="FLAG{regtest_" + uuid.uuid4().hex[:6] + "}", value=100.0,
                   author=author, byoc=True, description="f", challenges=[chall])
    db.commit()

    # createSolve returns a message string either way; a successful solve says
    # "<user> solved <flag> for <n> points", a refusal explains itself.
    msg = str(db.createSolve(user=solver, flag=flag))
    check("a different team CAN solve it", "solved" in msg and "trying to submit" not in msg, msg)

    msg2 = str(db.createSolve(user=author, flag=flag))
    check("the author CANNOT solve their own", "trying to submit" in msg2, msg2)


if __name__ == "__main__":
    print("db: " + TEST_DB)
    seed()
    test_quickreg_shape()
    test_rejections()
    test_google_path()
    test_cross_team_solve()
    print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
    if FAIL:
        print("failed: " + ", ".join(FAIL))
    sys.exit(1 if FAIL else 0)
