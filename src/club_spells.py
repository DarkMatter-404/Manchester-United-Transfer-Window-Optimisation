"""When did a player's current spell at a club begin?

Clubs are identified by their id in the transfer records, never by a shared
word in their names. A club "organisation" is the senior club together with
its own youth and reserve sides. Which sides belong to which senior club is
decided once, by club_families(), and written to a table that can be read
and checked. Two clubs that merely look alike ("Real Unión" and
"Real Sociedad", "Man City U21" and "Man Utd") are different organisations.

The two-year rule needs the start of the spell the player is in on the
cutoff date, so these cases are told apart:

    a new signing after an earlier spell      the spell starts at the new signing
    a loan that was then made permanent       the spell starts when the loan began
    a return from loan to the owning club     the spell started before the loan
    a move up from the club's own youth side  the spell starts when the player
                                              joined the organisation
    a signing from another club's youth side  an ordinary signing

A move is a dictionary with: date, from_id, from_name, to_id, to_name, fee.
"""

import datetime
import itertools
import re
import unicodedata

# Endings that mark a youth or reserve side in the source's club names
YOUTH_ENDING = re.compile(
    r" (U[0-9]{2}|II|III|B|C|2|Y|Yth\.?|Youth|Jgd\.?|Res\.?|Reserves|Sub-[0-9]{2}|Castilla|Next Gen"
    r"|Futuro|Primavera|Promesas|Atlètic|Atletic|Academy)$")

# A loan return and the permanent signing that follows it are normally dated a
# day apart; allow some slack for late paperwork
MADE_PERMANENT_WITHIN_DAYS = 62


def plain(name):
    """Lower-case a club name without accents, so 'Atlètic' and 'Atletic' compare equal."""
    text = unicodedata.normalize("NFKD", name)
    return "".join(c for c in text if not unicodedata.combining(c)).strip().lower()


def youth_stem(name):
    """The name without its youth or reserve ending, or None if it has no such ending."""
    if name is None or YOUTH_ENDING.search(name) is None:
        return None
    return plain(YOUTH_ENDING.sub("", name))


def club_families(names_of, senior_ids, extra_aliases, extra_sides):
    """Decide which youth and reserve sides belong to which senior club.

    names_of        club id -> every name the club is recorded under
    senior_ids      the clubs whose organisations are needed
    extra_aliases   senior club id -> short names, entered by hand, that the
                    club's own sides use before a youth ending ("Milan" in "Milan U19")
    extra_sides     side club id -> senior club id, entered by hand, for a side
                    whose name has no youth ending ("Bilbao Athletic")

    A side belongs to a senior club only if one of its names is exactly one of
    the senior club's names followed by a youth or reserve ending. A side that
    would belong to two senior clubs is not assigned and is reported instead.

    Returns (rows, ambiguous): rows are (member id, senior id, basis), sorted.
    """
    alias_owner = {}      # plain alias -> set of senior ids
    for senior in sorted(senior_ids):
        aliases = set(plain(n) for n in names_of.get(senior, []))
        aliases.update(plain(n) for n in extra_aliases.get(senior, []))
        for alias in aliases:
            alias_owner.setdefault(alias, set()).add(senior)

    rows = []
    ambiguous = []
    for club in sorted(names_of):
        if club in senior_ids:
            continue
        if club in extra_sides:
            rows.append((club, extra_sides[club], "entered by hand after review"))
            continue
        owners = set()
        matched = ""
        for name in sorted(names_of[club]):
            stem = youth_stem(name)
            if stem is not None and stem in alias_owner:
                owners.update(alias_owner[stem])
                matched = name
        if len(owners) == 1:
            rows.append((club, owners.pop(), "name '" + matched + "' is one of the senior club's names with a youth ending"))
        elif len(owners) > 1:
            ambiguous.append((club, sorted(owners)))
    return rows, ambiguous


def days_between(earlier, later):
    return (datetime.date.fromisoformat(later[:10]) - datetime.date.fromisoformat(earlier[:10])).days


def no_fee(move):
    """True if no fee is recorded, as with a loan, a loan return or a free transfer."""
    return move["fee"] is None or move["fee"] != move["fee"] or move["fee"] == 0


def order_moves(moves):
    """Sort moves by date, and put moves made on the same day in a chain.

    On a day with several moves, the moves are ordered so that each one starts
    where the one before it ended (for example, a signing and a loan back to
    the selling club on the same day). If there is no such order, or more than
    one, the day is reported as ambiguous and a fixed fallback order is used.

    Returns (ordered moves, list of ambiguous dates).
    """
    by_date = {}
    for move in moves:
        by_date.setdefault(move["date"], []).append(move)

    ordered = []
    ambiguous = []
    for date in sorted(by_date):
        group = sorted(by_date[date], key=lambda m: (m["from_id"], m["to_id"], m["fee"] or 0))
        if len(group) == 1:
            ordered.extend(group)
            continue
        location = ordered[-1]["to_id"] if ordered else None
        chains = []
        for order in itertools.permutations(group):
            linked = all(order[i]["to_id"] == order[i + 1]["from_id"] for i in range(len(order) - 1))
            starts_right = location is None or order[0]["from_id"] == location
            if linked and starts_right:
                chains.append(list(order))
        if len(chains) == 1:
            ordered.extend(chains[0])
        else:
            ambiguous.append(date)
            ordered.extend(group)
    return ordered, ambiguous


def current_spell(moves, family, senior_id):
    """Return (start date, basis) of the player's current spell in a club organisation.

    moves must already be in order (see order_moves). family is the set of club
    ids of the organisation: the senior club and its own youth and reserve sides.
    The start date is None when the records do not show one.
    """
    into = [i for i, m in enumerate(moves) if m["to_id"] in family and m["from_id"] not in family]
    inside = [i for i, m in enumerate(moves) if m["to_id"] in family and m["from_id"] in family]
    if not into:
        if inside:
            return None, "came through the club's youth system; entry not on record"
        return None, "no move into the club on record"

    position = into[-1]
    while True:
        arrival = moves[position]

        # A return from loan: the player had left this organisation for the
        # same club earlier, and neither move carries a fee
        loan_out = None
        for i in range(position):
            if moves[i]["from_id"] in family and moves[i]["to_id"] == arrival["from_id"]:
                loan_out = i
        if loan_out is not None and no_fee(moves[loan_out]) and no_fee(arrival):
            before = [i for i in into if i < loan_out]
            if not before:
                return None, "at the club before a loan; joining not on record"
            position = before[-1]
            continue

        # A loan made permanent: the player was already here on loan, was
        # returned on paper to the lending club and signed straight back
        returned = None
        for i in range(position):
            earlier = moves[i]
            if (earlier["from_id"] in family and earlier["to_id"] == arrival["from_id"] and no_fee(earlier)
                    and 0 <= days_between(earlier["date"], arrival["date"]) <= MADE_PERMANENT_WITHIN_DAYS):
                returned = i
        if returned is not None:
            before = [i for i in into if i < returned]
            if before:
                position = before[-1]
                continue

        # Otherwise this move is the start of the current spell
        if arrival["to_id"] != senior_id:
            side = "joined the club's youth or reserve side from another club"
            return arrival["date"], side + (" (no recorded fee)" if no_fee(arrival) else " (for a fee)")
        if no_fee(arrival):
            return arrival["date"], "arrived without a recorded fee (loan or free transfer)"
        return arrival["date"], "signed for a fee"


def in_club_by(moves, family, first_appearance):
    """Earliest dated record that puts the player inside the organisation.

    Used when the start of the spell is not on record. A move out of the
    organisation (for example on loan), a move between its own sides, or a
    match for the club each show that the player was already there on that date.

    Returns (date, evidence) or (None, "").
    """
    records = []
    for move in moves:
        if move["from_id"] in family and move["to_id"] in family:
            records.append((move["date"], "move between the club's own sides"))
        elif move["from_id"] in family:
            records.append((move["date"], "move out of the club, for example on loan"))
    if first_appearance:
        records.append((first_appearance, "first match for the club"))
    if not records:
        return None, ""
    return sorted(records)[0]


def two_year_status(info, override, signed_since):
    """Classify a candidate for the two-year rule from the start of the current spell.

    info       a row of players_at_cutoff.csv
    override   a row of joining_date_overrides.csv for this player, or None
    Returns "eligible", "joined within two years" or "not verified", with the evidence used.

    The exact start date is not needed if a dated record shows the player was
    already in the club's organisation before the threshold. Without such a
    record the case is "not verified" and is treated as not eligible.
    """
    if override is not None:
        status = "joined within two years" if override["joined_club_date"] >= signed_since else "eligible"
        return status, "entered by hand: " + override["basis"]
    if info["history_flag"] != "":
        return "not verified", info["history_flag"]
    if info["joined_club_date"] != "":
        status = "joined within two years" if info["joined_club_date"] >= signed_since else "eligible"
        return status, info["joined_basis"]
    if info["in_club_by_date"] != "" and info["in_club_by_date"] < signed_since:
        return "eligible", (info["joined_basis"] + "; in the club by " + info["in_club_by_date"]
                            + " (" + info["in_club_by_evidence"] + ")")
    return "not verified", info["joined_basis"] + "; no dated record in the club before " + signed_since
